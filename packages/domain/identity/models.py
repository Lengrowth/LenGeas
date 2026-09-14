"""Identity model independent from providers and persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class IdentityKind(StrEnum):
    SUPABASE = "supabase"
    GUEST = "guest"


@dataclass(slots=True)
class Account:
    account_id: str
    created_at: datetime
    email_hash: str | None = None
    deleted_at: datetime | None = None
    restricted: bool = False
    session_epoch: int = 0


@dataclass(slots=True)
class StudioPlayer:
    player_id: str
    created_at: datetime
    deleted_at: datetime | None = None
    tombstone: bool = False


@dataclass(slots=True)
class PlayerIdentity:
    identity_id: str
    player_id: str
    kind: IdentityKind
    provider: str
    subject_or_credential_hash: str
    created_at: datetime
    revoked_at: datetime | None = None
    device_key_fingerprint: str | None = None
    account_id: str | None = None


@dataclass(slots=True)
class GameProfile:
    profile_id: str
    player_id: str
    studio_id: str
    game_id: str
    state: dict[str, object] = field(default_factory=dict)
    entitlements: set[str] = field(default_factory=set)
    state_version: int = 0


@dataclass(slots=True)
class GlobalProfile:
    player_id: str
    entitlements: set[str] = field(default_factory=set)
    cosmetics: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    actor_id: str
    action: str
    studio_id: str | None
    subject_id: str | None
    occurred_at: datetime
    metadata: dict[str, str]
