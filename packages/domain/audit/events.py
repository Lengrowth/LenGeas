"""PII-safe versioned event envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


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
        forbidden = {"token", "authorization", "password", "secret", "api_key", "email", "ip"}
        safe_payload = {
            key: value for key, value in (payload or {}).items() if key.lower() not in forbidden
        }
        return cls(
            str(uuid4()),
            event_type,
            datetime.now(UTC),
            producer,
            studio_id,
            game_id,
            player_id,
            correlation_id or str(uuid4()),
            causation_id,
            safe_payload,
        )
