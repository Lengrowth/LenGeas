"""Provider-independent HTTP API used only by the hosted E2E gate."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from apps.api.app.auth.jwt import JwtClaims
from apps.api.app.main import create_app
from packages.domain.identity.models import IdentityKind
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, Membership, MembershipRole, TrustedScope
from packages.domain.tenancy.repository import InMemoryTenantRepository


class HostedTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return proof in {"ci-e2e-proof", "ci-e2e-lifecycle-proof"}


class HostedJwt:
    async def verify(self, token: str) -> JwtClaims:
        if token != "ci-e2e-token":
            raise ValueError("invalid_token")
        return JwtClaims(
            "ci-e2e-subject",
            "https://ci.example.test",
            "ci",
            "ci-e2e-jti",
            {
                "sub": "ci-e2e-subject",
                "amr": ["mfa"],
                "aal": "aal2",
            },
        )


class HostedProvider:
    async def verify(self, provider: str, subject: str, proof: str) -> bool:
        return (
            provider == "supabase"
            and subject == "ci-linked-subject"
            and proof == "ci-provider-proof"
        )


identity = InMemoryIdentityRepository()
tenancy = InMemoryTenantRepository()
account = identity.create_account("ci-email-hash")
target = identity.create_player()
account.player_id = target.player_id
identity.link_identity(
    target.player_id,
    IdentityKind.SUPABASE,
    "supabase",
    "ci-e2e-subject",
    account_id=account.account_id,
)
source = identity.create_player()
source_credential = "ci-e2e-source-credential-000000000000"
source_identity = identity.link_identity(
    source.player_id,
    IdentityKind.GUEST,
    "device",
    "ci-e2e-source-credential-hash",
    device_fingerprint="ci-e2e-source-device",
)
identity.save_guest_credential(
    source_identity.identity_id,
    hashlib.sha256(source_credential.encode()).hexdigest(),
    "ci-e2e-source-device-key",
)
scope = TrustedScope(
    account.account_id,
    "ci-e2e-studio",
    "ci-e2e-game",
    Environment.TESTING,
    frozenset({MembershipRole.ADMIN}),
    mfa_verified=True,
    game_ids=frozenset({"ci-e2e-game"}),
    environments=frozenset({Environment.TESTING}),
)
identity.create_profile(scope, target.player_id, "ci-e2e-game")
identity.create_profile(scope, source.player_id, "ci-e2e-game")
secondary = identity.create_account("ci-secondary-email-hash")
tenancy.memberships["ci-e2e-membership"] = Membership(
    "ci-e2e-membership",
    "ci-e2e-studio",
    account.account_id,
    MembershipRole.ADMIN,
    datetime.now(UTC),
    game_ids=frozenset({"ci-e2e-game"}),
)

app = create_app(
    identity=identity,
    tenancy=tenancy,
    test_mode=True,
    turnstile=HostedTurnstile(),
    jwt_verifier=HostedJwt(),
    provider_verifier=HostedProvider(),
)


@app.get("/__e2e/metadata")
async def e2e_metadata() -> dict[str, str]:
    return {
        "target_player_id": target.player_id,
        "source_player_id": source.player_id,
        "source_credential": source_credential,
        "secondary_account_id": secondary.account_id,
    }
