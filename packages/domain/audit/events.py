"""PII-safe versioned event envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from packages.domain.ids import new_uuid7

_FORBIDDEN = {
    "token",
    "accesstoken",
    "refreshtoken",
    "authorization",
    "password",
    "secret",
    "apikey",
    "credential",
    "credentialhash",
    "email",
    "emailaddress",
    "phone",
    "phonenumber",
    "ip",
    "ipaddress",
    "address",
    "name",
}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if str(key).lower().replace("_", "").replace("-", "") in _FORBIDDEN
            else _scrub(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: str
    event_type: str
    occurred_at: datetime
    producer: str
    studio_id: str | None
    game_id: str | None
    player_id: str | None
    correlation_id: str
    causation_id: str | None
    payload: dict[str, Any]

    @classmethod
    def create(
        cls,
        event_type: str,
        producer: str,
        *,
        studio_id: str | None = None,
        game_id: str | None = None,
        player_id: str | None = None,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> EventEnvelope:
        if event_type not in {
            "identity.guest_created.v1",
            "identity.linked.v1",
            "identity.merged.v1",
            "studio.membership_changed.v1",
            "privacy.requested.v1",
        }:
            raise ValueError("event_type_not_registered")
        safe_payload = _scrub(payload or {})
        return cls(
            new_uuid7(),
            event_type,
            datetime.now(UTC),
            producer,
            studio_id,
            game_id,
            player_id,
            correlation_id or new_uuid7(),
            causation_id,
            safe_payload,
        )
