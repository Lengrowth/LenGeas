"""Application boundary for plans, idempotency, receipts, and state commits."""

from __future__ import annotations

import copy
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from packages.runtime.src.lengeas_runtime.actions import ActionPlan
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.events import OutboxRecord
from packages.runtime.src.lengeas_runtime.serialization import digest, thaw_value


@dataclass(frozen=True, slots=True)
class ActionReceipt:
    receipt_id: str
    actor_id: str
    studio_id: str
    game_id: str
    player_id: str
    action_id: str
    input_digest: str
    definition_digest: str
    engine_version: str
    prior_state_version: int
    state_version: int
    state_digest: str
    logical_time: str
    seed: int
    status: str
    explanation: Mapping[str, Any]
    event_ids: tuple[str, ...]


class ActionRepository(Protocol):
    def commit_action(
        self,
        *,
        state_key: tuple[str, str, str],
        expected_version: int,
        idempotency_key: str,
        fingerprint: str,
        actor_id: str,
        plan: ActionPlan,
        receipt: ActionReceipt,
        outbox: tuple[OutboxRecord, ...],
    ) -> ActionReceipt: ...


def _apply(state: dict[str, Any], plan: ActionPlan) -> dict[str, Any]:
    result = copy.deepcopy(state)
    for operation in plan.operations:
        if operation.path is None:
            continue
        parts = operation.path.split(".")
        cursor = result
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        key = parts[-1]
        value = thaw_value(operation.value)
        if operation.kind in {"increment", "grant", "grant_item"}:
            cursor[key] = cursor.get(key, 0) + (value or 0)
        elif operation.kind == "decrement":
            cursor[key] = cursor.get(key, 0) - (value or 0)
        elif operation.kind == "set":
            cursor[key] = value
        elif operation.kind == "append_unique":
            values = list(cursor.get(key, []))
            if value not in values:
                values.append(value)
            cursor[key] = values
        elif operation.kind == "remove":
            cursor.pop(key, None)
        else:
            cursor[key] = value
    return result


class InMemoryActionRepository:
    """Atomic test adapter mirroring the Mongo transaction boundary."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.states: dict[tuple[str, str, str], tuple[int, dict[str, Any]]] = {}
        self.receipts: dict[str, ActionReceipt] = {}
        self.idempotency: dict[tuple[str, str, str, str, str], tuple[str, ActionReceipt]] = {}
        self.outbox: dict[str, OutboxRecord] = {}

    def seed_state(self, key: tuple[str, str, str], state: Mapping[str, Any]) -> None:
        with self._lock:
            self.states[key] = (0, copy.deepcopy(dict(state)))

    def commit_action(
        self,
        *,
        state_key: tuple[str, str, str],
        expected_version: int,
        idempotency_key: str,
        fingerprint: str,
        actor_id: str,
        plan: ActionPlan,
        receipt: ActionReceipt,
        outbox: tuple[OutboxRecord, ...],
    ) -> ActionReceipt:
        with self._lock:
            idem_key = (*state_key, actor_id, idempotency_key)
            existing = self.idempotency.get(idem_key)
            if existing is not None:
                if existing[0] != fingerprint:
                    raise RuntimeErrorCode("idempotency_conflict")
                return existing[1]
            version, state = self.states.get(state_key, (0, {}))
            if version != expected_version:
                raise RuntimeErrorCode("state_conflict")
            new_state = _apply(state, plan)
            updated = ActionReceipt(
                receipt.receipt_id,
                receipt.actor_id,
                receipt.studio_id,
                receipt.game_id,
                receipt.player_id,
                receipt.action_id,
                receipt.input_digest,
                receipt.definition_digest,
                receipt.engine_version,
                version,
                version + 1,
                digest(new_state),
                receipt.logical_time,
                receipt.seed,
                receipt.status,
                receipt.explanation,
                receipt.event_ids,
            )
            self.states[state_key] = (version + 1, new_state)
            self.receipts[updated.receipt_id] = updated
            self.idempotency[idem_key] = (fingerprint, updated)
            for record in outbox:
                self.outbox[record.event_id] = record
            return updated

    def receipt(self, scope: tuple[str, str, str], receipt_id: str) -> ActionReceipt | None:
        with self._lock:
            receipt = self.receipts.get(receipt_id)
            if receipt is None or (receipt.studio_id, receipt.game_id, receipt.player_id) != scope:
                return None
            return receipt

    def state(self, key: tuple[str, str, str]) -> tuple[int, dict[str, Any]] | None:
        with self._lock:
            result = self.states.get(key)
            return copy.deepcopy(result) if result is not None else None
