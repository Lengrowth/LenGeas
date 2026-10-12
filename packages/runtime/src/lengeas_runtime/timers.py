"""Pure timer plan construction from supplied logical time."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode


@dataclass(frozen=True, slots=True)
class TimerPlan:
    timer_id: str
    due_at: datetime
    authority: str
    definition_digest: str
    payload: tuple[tuple[str, str], ...] = ()


def plan_timer(
    timer_id: str, now: datetime, duration_ms: int, authority: str, definition_digest: str
) -> TimerPlan:
    if (
        now.tzinfo is None
        or duration_ms < 0
        or authority not in {"server", "match_server", "local"}
    ):
        raise RuntimeErrorCode("timer_plan_invalid")
    return TimerPlan(
        timer_id, now + timedelta(milliseconds=duration_ms), authority, definition_digest
    )
