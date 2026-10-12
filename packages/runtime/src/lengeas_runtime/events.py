"""Deterministic event drafts and transactional outbox/inbox contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.runtime.src.lengeas_runtime.serialization import freeze_value


@dataclass(frozen=True, slots=True)
class EventDraft:
    ordinal: int
    event_type: str
    occurred_at: datetime
    producer: str
    studio_id: str
    game_id: str
    player_id: str
    definition_digest: str
    correlation_id: str
    causation_id: str | None
    payload: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    event_id: str
    event: EventDraft
    status: str = "pending"


@dataclass(frozen=True, slots=True)
class InboxKey:
    consumer: str
    event_id: str


def event_draft(
    ordinal: int,
    event_type: str,
    occurred_at: datetime,
    *,
    producer: str,
    studio_id: str,
    game_id: str,
    player_id: str,
    definition_digest: str,
    correlation_id: str,
    causation_id: str | None,
    payload: Mapping[str, Any],
) -> EventDraft:
    return EventDraft(
        ordinal,
        event_type,
        occurred_at,
        producer,
        studio_id,
        game_id,
        player_id,
        definition_digest,
        correlation_id,
        causation_id,
        tuple(sorted((key, freeze_value(value)) for key, value in payload.items())),
    )
