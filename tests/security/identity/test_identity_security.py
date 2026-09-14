from __future__ import annotations

import asyncio
import base64
import unittest
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from apps.api.app.auth.guest import GuestIdentityService
from apps.api.app.auth.jwt import JwtClaims
from apps.api.app.auth.mapping import InternalAccountMapper
from apps.api.app.main import create_app
from packages.domain.audit.events import EventEnvelope
from packages.domain.authorization.policy import (
    Actor,
    ActorKind,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.identity.merge import MergeService
from packages.domain.identity.privacy import PrivacyOperation, PrivacyService
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, Membership, MembershipRole, TrustedScope
from packages.domain.tenancy.repository import InMemoryTenantRepository


class FakeTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return proof == "provider-valid"


class FakeJwt:
    async def verify(self, token: str) -> JwtClaims:
        if token != "verified-token":
            raise ValueError("invalid_token")
        return JwtClaims("subject-1", "issuer", "audience", "jti-1", {"sub": "subject-1"})


class FakeProvider:
    async def verify(self, provider: str, subject: str, proof: str) -> bool:
        return proof == "provider-proof"


class IdentitySecurityTests(unittest.TestCase):
    def test_forged_tenant_scope_is_denied(self) -> None:
        actor = Actor(
            "a", ActorKind.ACCOUNT, "studio-a", frozenset({MembershipRole.ADMIN}), mfa_verified=True
        )
        request = PolicyRequest(
            actor, "write", Resource("studio", "s", "studio-b"), Environment.TESTING
        )
        self.assertEqual(PolicyDecisionService().decide(request).code, "tenant_mismatch")

    def test_expired_support_grant_and_mfa_bypass_are_denied(self) -> None:
        expired = Actor(
            "a",
            ActorKind.ACCOUNT,
            "studio-a",
            frozenset({MembershipRole.SUPPORT}),
            support_case_id="c",
            support_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        decision = PolicyDecisionService().decide(
            PolicyRequest(expired, "read", Resource("player", "p", "studio-a"), Environment.TESTING)
        )
        self.assertEqual(decision.code, "support_grant_expired")
        operator = Actor(
            "a",
            ActorKind.ACCOUNT,
            "studio-a",
            frozenset({MembershipRole.ADMIN}),
            mfa_verified=False,
        )
        decision = PolicyDecisionService().decide(
            PolicyRequest(
                operator, "admin", Resource("studio", "s", "studio-a"), Environment.TESTING
            )
        )
        self.assertEqual(decision.code, "mfa_required")

    def test_protected_route_rejects_forged_headers(self) -> None:
        client = TestClient(
            create_app(test_mode=True, turnstile=FakeTurnstile(), jwt_verifier=FakeJwt())
        )
        response = client.post(
            "/api/v1/studios",
            json={"name": "x", "slug": "studio-x"},
            headers={"x-actor-id": "forged", "x-studio-id": "forged"},
        )
        self.assertEqual(response.status_code, 401)

    def test_default_turnstile_fails_closed(self) -> None:
        private = Ed25519PrivateKey.generate()
        key = (
            base64.urlsafe_b64encode(private.public_key().public_bytes_raw()).rstrip(b"=").decode()
        )
        response = TestClient(create_app(test_mode=True)).post(
            "/api/v1/auth/guests",
            json={"turnstile_proof": "arbitrary", "device_public_key": key},
            headers={"Idempotency-Key": "guest-test-0001"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "turnstile_failed")

    def test_recovery_replaces_device_key_and_credential(self) -> None:
        private = Ed25519PrivateKey.generate()
        old = (
            base64.urlsafe_b64encode(private.public_key().public_bytes_raw()).rstrip(b"=").decode()
        )
        replacement = Ed25519PrivateKey.generate()
        new = (
            base64.urlsafe_b64encode(replacement.public_key().public_bytes_raw())
            .rstrip(b"=")
            .decode()
        )
        repo = InMemoryIdentityRepository()
        service = GuestIdentityService(repo, FakeTurnstile())
        credentials = asyncio.run(service.create("provider-valid", old))
        challenge = b"challenge"
        rotated = service.recover(credentials.identity_id, private.sign(challenge), challenge, new)
        self.assertNotEqual(rotated, credentials.refresh_token)
        with self.assertRaisesRegex(ValueError, "credential_invalid"):
            service.rotate(credentials.identity_id, credentials.refresh_token)

    def test_privacy_tombstone_removes_pii_and_blocks_mapping(self) -> None:
        repo = InMemoryIdentityRepository()
        account = repo.create_account("email-hash")
        player = repo.create_player()
        repo.link_identity(
            player.player_id, "supabase", "supabase", "subject-1", account_id=account.account_id
        )  # type: ignore[arg-type]
        privacy = PrivacyService(repo)
        request = privacy.request(account.account_id, PrivacyOperation.DELETION)
        privacy.execute_deletion(request.request_id)
        self.assertIsNone(account.email_hash)
        with self.assertRaisesRegex(KeyError, "mapped_account_missing"):
            InternalAccountMapper(repo).map_subject("subject-1")

    def test_nested_event_payload_is_redacted(self) -> None:
        event = EventEnvelope.create(
            "privacy.requested.v1",
            "test",
            payload={"nested": {"token": "secret", "email": "synthetic@example.test"}},
        )
        self.assertEqual(event.payload["nested"]["token"], "[REDACTED]")
        self.assertEqual(event.payload["nested"]["email"], "[REDACTED]")

    def test_session_revocation_rejects_the_same_jwt(self) -> None:
        identity = InMemoryIdentityRepository()
        account = identity.create_account()
        player = identity.create_player()
        account.player_id = player.player_id
        identity.link_identity(
            player.player_id, "supabase", "supabase", "subject-1", account_id=account.account_id
        )  # type: ignore[arg-type]
        tenancy = InMemoryTenantRepository()
        tenancy.memberships["membership"] = Membership(
            "membership", "studio", account.account_id, MembershipRole.ADMIN, datetime.now(UTC)
        )
        client = TestClient(
            create_app(identity=identity, tenancy=tenancy, jwt_verifier=FakeJwt(), test_mode=True)
        )
        headers = {
            "Authorization": "Bearer verified-token",
            "x-studio-id": "studio",
            "Idempotency-Key": "revoke-0001",
        }
        self.assertEqual(client.get("/api/v1/auth/current", headers=headers).status_code, 200)
        self.assertEqual(client.post("/api/v1/sessions/revoke", headers=headers).status_code, 204)
        self.assertEqual(client.get("/api/v1/auth/current", headers=headers).status_code, 401)

    def test_merge_requires_owner_and_both_guest_proofs(self) -> None:
        identity = InMemoryIdentityRepository()
        account = identity.create_account()
        actor = identity.create_player()
        account.player_id = actor.player_id
        identity.link_identity(
            actor.player_id, "supabase", "supabase", "subject-1", account_id=account.account_id
        )  # type: ignore[arg-type]
        source, target = identity.create_player(), identity.create_player()
        scope = TrustedScope(
            "actor", "studio", "game", Environment.TESTING, frozenset({MembershipRole.ADMIN})
        )
        identity.create_profile(scope, source.player_id, "game")
        identity.create_profile(scope, target.player_id, "game")
        tenancy = InMemoryTenantRepository()
        tenancy.memberships["membership"] = Membership(
            "membership",
            "studio",
            account.account_id,
            MembershipRole.ADMIN,
            datetime.now(UTC),
            game_ids=frozenset({"game"}),
        )
        client = TestClient(
            create_app(identity=identity, tenancy=tenancy, jwt_verifier=FakeJwt(), test_mode=True)
        )
        response = client.post(
            "/api/v1/players/merge/preview",
            json={"source_player_id": source.player_id, "target_player_id": target.player_id},
            headers={
                "Authorization": "Bearer verified-token",
                "x-studio-id": "studio",
                "Idempotency-Key": "merge-0001",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_identity_link_uses_mapped_player_and_provider_control(self) -> None:
        identity = InMemoryIdentityRepository()
        account = identity.create_account()
        player = identity.create_player()
        account.player_id = player.player_id
        identity.link_identity(
            player.player_id, "supabase", "supabase", "subject-1", account_id=account.account_id
        )  # type: ignore[arg-type]
        tenancy = InMemoryTenantRepository()
        tenancy.memberships["membership"] = Membership(
            "membership", "studio", account.account_id, MembershipRole.ADMIN, datetime.now(UTC)
        )
        client = TestClient(
            create_app(
                identity=identity,
                tenancy=tenancy,
                jwt_verifier=FakeJwt(),
                provider_verifier=FakeProvider(),
                test_mode=True,
            )
        )
        headers = {
            "Authorization": "Bearer verified-token",
            "x-studio-id": "studio",
            "Idempotency-Key": "link-0001",
        }
        denied = client.post(
            "/api/v1/auth/identity-links",
            json={"provider": "steam", "subject": "s-1"},
            headers=headers,
        )
        self.assertEqual(denied.status_code, 403)
        allowed = client.post(
            "/api/v1/auth/identity-links",
            json={"provider": "steam", "subject": "s-1", "provider_proof": "provider-proof"},
            headers=headers,
        )
        self.assertEqual(allowed.status_code, 201)

    def test_concurrent_guest_proof_is_consumed_once(self) -> None:
        async def run() -> list[object]:
            service = GuestIdentityService(InMemoryIdentityRepository(), FakeTurnstile())
            keys = []
            for _ in range(2):
                private = Ed25519PrivateKey.generate()
                keys.append(
                    base64.urlsafe_b64encode(private.public_key().public_bytes_raw())
                    .rstrip(b"=")
                    .decode()
                )
            return await asyncio.gather(
                service.create("provider-valid", keys[0]),
                service.create("provider-valid", keys[1]),
                return_exceptions=True,
            )

        results = asyncio.run(run())
        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(sum(isinstance(result, ValueError) for result in results), 1)

    def test_merge_idempotency_binds_payload(self) -> None:
        repo = InMemoryIdentityRepository()
        scope = TrustedScope(
            "actor", "studio", "game", Environment.TESTING, frozenset({MembershipRole.OWNER})
        )
        source1, target1 = repo.create_player(), repo.create_player()
        source2, target2 = repo.create_player(), repo.create_player()
        for player in (source1, target1, source2, target2):
            repo.create_profile(scope, player.player_id, "game")
        service = MergeService(repo)
        first = service.preview(scope, source1.player_id, target1.player_id)
        second = service.preview(scope, source2.player_id, target2.player_id)
        service.commit(scope, first.preview_id, {"game": "target"}, "same-key")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            service.commit(scope, second.preview_id, {"game": "target"}, "same-key")

    def test_service_revocation_emits_tenant_bound_event(self) -> None:
        repo = InMemoryTenantRepository()
        scope = TrustedScope(
            "actor",
            "studio",
            None,
            Environment.TESTING,
            frozenset({MembershipRole.ADMIN}),
            mfa_verified=True,
        )
        account = repo.create_service_account(scope, "worker", frozenset({"player:read"}))
        before = len(repo.events)
        repo.revoke_service_account(scope, account.service_account_id)
        self.assertGreater(len(repo.events), before)
        self.assertFalse(repo.verify_service_credential(account.service_account_id, "wrong"))
