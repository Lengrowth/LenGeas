"""Approved, scoped, idempotent cross-game reward delivery contracts."""

from __future__ import annotations

import copy
import threading
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from packages.domain.ids import new_uuid7


class CrossGameError(ValueError):
    """A cross-game contract, event, or delivery violates its allowlist."""


@dataclass(frozen=True, slots=True)
class CrossGameContract:
    contract_id: str
    studio_id: str
    source_game_id: str
    target_game_id: str
    event_types: frozenset[str]
    target_action_id: str
    payload_fields: frozenset[str]
    reward_limits: Mapping[str, int]
    max_deliveries_per_player: int
    status: str
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if (
            not self.contract_id
            or not self.studio_id
            or not self.source_game_id
            or not self.target_game_id
            or self.source_game_id == self.target_game_id
            or not self.target_action_id
            or not self.event_types
            or not 1 <= self.max_deliveries_per_player <= 100_000
        ):
            raise CrossGameError("invalid_cross_game_contract")
        if any(not item or amount < 0 for item, amount in self.reward_limits.items()):
            raise CrossGameError("invalid_cross_game_reward_limits")


@dataclass(frozen=True, slots=True)
class SourceEvent:
    event_id: str
    event_type: str
    studio_id: str
    game_id: str
    player_id: str
    payload: Mapping[str, Any]
    definition_digest: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class CrossGameDelivery:
    delivery_id: str
    contract_id: str
    source_event_id: str
    source_player_id: str
    target_player_id: str
    target_game_id: str
    target_action_id: str
    payload: Mapping[str, Any]
    idempotency_key: str
    delivered_at: datetime


class InMemoryCrossGameService:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._contracts: dict[str, CrossGameContract] = {}
        self._deliveries: dict[tuple[str, str], CrossGameDelivery] = {}
        self._counts: dict[tuple[str, str], int] = defaultdict(int)

    def approve(self, contract: CrossGameContract) -> None:
        if contract.status != "approved":
            raise CrossGameError("contract_not_approved")
        with self._lock:
            graph: dict[str, set[str]] = defaultdict(set)
            for current in self._contracts.values():
                if current.status == "approved" and current.revoked_at is None:
                    graph[current.source_game_id].add(current.target_game_id)
            graph[contract.source_game_id].add(contract.target_game_id)
            if self._has_cycle(graph):
                raise CrossGameError("cross_game_reward_cycle")
            self._contracts[contract.contract_id] = contract

    @staticmethod
    def _has_cycle(graph: Mapping[str, set[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for neighbor in graph.get(node, set()):
                if visit(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)

    def revoke(self, contract_id: str) -> CrossGameContract:
        with self._lock:
            current = self._contracts.get(contract_id)
            if current is None:
                raise CrossGameError("contract_not_found")
            updated = CrossGameContract(
                current.contract_id,
                current.studio_id,
                current.source_game_id,
                current.target_game_id,
                current.event_types,
                current.target_action_id,
                current.payload_fields,
                current.reward_limits,
                current.max_deliveries_per_player,
                "revoked",
                current.expires_at,
                datetime.now(UTC),
            )
            self._contracts[contract_id] = updated
            return updated

    def deliver(
        self,
        contract_id: str,
        event: SourceEvent,
        target_player_id: str,
        *,
        target_action: Callable[[str, str, Mapping[str, Any]], Any],
    ) -> CrossGameDelivery:
        key = (contract_id, event.event_id)
        with self._lock:
            previous = self._deliveries.get(key)
            if previous is not None:
                return previous
            contract = self._contracts.get(contract_id)
            now = datetime.now(UTC)
            if contract is None or contract.status != "approved" or contract.revoked_at is not None:
                raise CrossGameError("contract_not_approved")
            if contract.expires_at is not None and contract.expires_at <= now:
                raise CrossGameError("contract_expired")
            if (
                event.studio_id != contract.studio_id
                or event.game_id != contract.source_game_id
                or event.event_type not in contract.event_types
                or not event.event_id
                or not event.player_id
                or not target_player_id
            ):
                raise CrossGameError("source_event_not_authorized")
            if set(event.payload) - contract.payload_fields:
                raise CrossGameError("source_payload_not_authorized")
            for resource, amount in event.payload.items():
                if resource in contract.reward_limits and (
                    not isinstance(amount, int)
                    or isinstance(amount, bool)
                    or amount < 0
                    or amount > contract.reward_limits[resource]
                ):
                    raise CrossGameError("delivery_reward_limit_exceeded")
            count_key = (contract_id, event.player_id)
            if self._counts[count_key] >= contract.max_deliveries_per_player:
                raise CrossGameError("delivery_limit_exceeded")
            idem = f"cross-game:{contract_id}:{event.event_id}"
            result = target_action(
                contract.target_game_id, contract.target_action_id, event.payload
            )
            if result is False:
                raise CrossGameError("target_action_rejected")
            delivery = CrossGameDelivery(
                new_uuid7(),
                contract_id,
                event.event_id,
                event.player_id,
                target_player_id,
                contract.target_game_id,
                contract.target_action_id,
                copy.deepcopy(dict(event.payload)),
                idem,
                now,
            )
            self._deliveries[key] = delivery
            self._counts[count_key] += 1
            return delivery

    def deliveries(self) -> tuple[CrossGameDelivery, ...]:
        with self._lock:
            return tuple(self._deliveries.values())
