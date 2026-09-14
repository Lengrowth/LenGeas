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
from packages.domain.identity.privacy import PrivacyOperation, PrivacyService
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, MembershipRole


class FakeTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return proof == "provider-valid"


class FakeJwt:
    async def verify(self, token: str) -> JwtClaims:
        if token != "verified-token":
            raise ValueError("invalid_token")
        return JwtClaims("subject-1", "issuer", "audience", "jti-1", {"sub": "subject-1"})


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
