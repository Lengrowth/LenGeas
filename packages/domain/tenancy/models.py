"""Pure tenancy values.  Nothing in this module imports an adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    WRITER = "writer"
    ANALYST = "analyst"
    SUPPORT = "support"
    VIEWER = "viewer"
    AI_AGENT = "ai_agent"


@dataclass(frozen=True, slots=True)
class TrustedScope:
    """Scope minted after authentication and policy evaluation.

    Request fields are intentionally absent from this type.  Repositories accept
    this value rather than tenant/game strings supplied by a caller.
    """

    actor_id: str
    studio_id: str
    game_id: str | None
    environment: Environment
    roles: frozenset[MembershipRole] = frozenset()
    support_case_id: str | None = None
    expires_at: datetime | None = None
    service_account_id: str | None = None
    ai_agent_id: str | None = None
    mfa_verified: bool = False
    game_ids: frozenset[str] = frozenset()
    environments: frozenset[Environment] = frozenset()

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is not None and now >= self.expires_at


@dataclass(slots=True)
class Studio:
    studio_id: str
    name: str
    slug: str
    created_at: datetime
    restricted: bool = False


@dataclass(slots=True)
class Membership:
    membership_id: str
    studio_id: str
    account_id: str
    role: MembershipRole
    created_at: datetime
    mfa_required: bool = False
    active: bool = True
    game_ids: frozenset[str] = frozenset()


@dataclass(slots=True)
class ServiceAccount:
    service_account_id: str
    studio_id: str
    client_id: str
    name: str
    scopes: frozenset[str]
    created_at: datetime
    revoked_at: datetime | None = None
    credential_hash: str | None = None


@dataclass(slots=True)
class Invitation:
    invitation_id: str
    studio_id: str
    email_hash: str
    role: MembershipRole
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None = None
