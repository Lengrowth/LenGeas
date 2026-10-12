"""Conserving append-only economy ledger and serialized balance projection."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

from packages.domain.ids import new_uuid7

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
SYSTEM_ACCOUNTS = frozenset({"system_faucet", "system_sink", "system_treasury"})


class EconomyError(ValueError):
    """A value operation violated ledger or balance integrity."""


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    entry_id: str
    account_id: str
    asset_id: str
    amount: int
    balance_after: int


@dataclass(frozen=True, slots=True)
class LedgerTransaction:
    transaction_id: str
    studio_id: str
    game_id: str
    player_id: str
    idempotency_key: str
    reason: str
    source: str
    actor_id: str
    definition_digest: str
    entries: tuple[LedgerEntry, ...]
    occurred_at: datetime
    compensates_transaction_id: str | None = None


@dataclass(frozen=True, slots=True)
class EconomyAction:
    costs: Mapping[str, int] = field(default_factory=dict)
    grants: Mapping[str, int] = field(default_factory=dict)
    multipliers: Mapping[str, tuple[int, int]] = field(default_factory=dict)
    caps: Mapping[str, int] = field(default_factory=dict)
    overflow_routes: Mapping[str, tuple[str, int, int]] = field(default_factory=dict)
    overflow_policy: Literal["reject", "clamp", "route"] = "reject"


@dataclass(frozen=True, slots=True)
class EconomyActionReceipt:
    receipt_id: str
    transaction_id: str
    studio_id: str
    game_id: str
    player_id: str
    actor_id: str
    action_id: str
    idempotency_key: str
    status: str
    balances: Mapping[str, int]
    event_ids: tuple[str, ...]
    occurred_at: datetime


class OperationStatusUnknown(EconomyError):
    """Commit succeeded but the caller did not observe the response."""


def plan_economy_entries(
    action: EconomyAction, current_balances: Mapping[str, int], *, player_id: str
) -> tuple[tuple[str, str, int], ...]:
    """Build conserved player/faucet/sink/treasury postings using integer math."""
    if action.overflow_policy not in {"reject", "clamp", "route"}:
        raise EconomyError("invalid_overflow_policy")
    entries: list[tuple[str, str, int]] = []
    after_cost = dict(current_balances)
    for asset, cost in sorted(action.costs.items()):
        if not asset or isinstance(cost, bool) or not isinstance(cost, int) or cost < 0:
            raise EconomyError("invalid_cost")
        balance = after_cost.get(asset, 0)
        if balance < cost:
            raise EconomyError("insufficient_balance")
        after_cost[asset] = balance - cost
        if cost:
            entries.extend(
                ((f"player:{player_id}:{asset}", asset, -cost), ("system_sink", asset, cost))
            )
    for asset, base_amount in sorted(action.grants.items()):
        if (
            not asset
            or isinstance(base_amount, bool)
            or not isinstance(base_amount, int)
            or base_amount < 0
        ):
            raise EconomyError("invalid_grant")
        numerator, denominator = action.multipliers.get(asset, (1, 1))
        if (
            isinstance(numerator, bool)
            or isinstance(denominator, bool)
            or not isinstance(numerator, int)
            or not isinstance(denominator, int)
            or numerator < 0
            or denominator <= 0
        ):
            raise EconomyError("invalid_multiplier")
        amount = base_amount * numerator // denominator
        if amount > INT64_MAX:
            raise EconomyError("amount_overflow")
        current = after_cost.get(asset, 0)
        cap = action.caps.get(asset, INT64_MAX)
        if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0 or cap > INT64_MAX:
            raise EconomyError("invalid_balance_cap")
        overflow = max(0, current + amount - cap)
        if overflow and action.overflow_policy == "reject":
            raise EconomyError("balance_cap_exceeded")
        credited = amount - overflow if overflow else amount
        if overflow and action.overflow_policy == "clamp":
            pass
        elif overflow and action.overflow_policy == "route":
            route = action.overflow_routes.get(asset)
            if route is None:
                raise EconomyError("overflow_route_missing")
            target_asset, route_numerator, route_denominator = route
            if (
                not target_asset
                or target_asset == asset
                or isinstance(route_numerator, bool)
                or isinstance(route_denominator, bool)
                or route_numerator < 0
                or route_denominator <= 0
            ):
                raise EconomyError("overflow_route_invalid")
            target_amount = overflow * route_numerator // route_denominator
            if target_amount > INT64_MAX:
                raise EconomyError("amount_overflow")
            entries.extend(
                (
                    ("system_treasury", target_asset, -target_amount),
                    (f"player:{player_id}:{target_asset}", target_asset, target_amount),
                )
            )
            after_cost[target_asset] = after_cost.get(target_asset, 0) + target_amount
        if amount:
            entries.extend(
                (
                    ("system_faucet", asset, -amount),
                    (f"player:{player_id}:{asset}", asset, credited),
                )
            )
            if overflow:
                account = "system_treasury" if action.overflow_policy == "route" else "system_sink"
                entries.append((account, asset, overflow))
        after_cost[asset] = min(current + amount, cap)
    # Validate the whole action before a repository begins its transaction.
    by_asset: dict[str, int] = {}
    for _, asset, amount in entries:
        by_asset[asset] = by_asset.get(asset, 0) + amount
    if any(by_asset.values()):
        raise EconomyError("ledger_unbalanced")
    return tuple(entries)


def _fingerprint(entries: Iterable[tuple[str, str, int]], reason: str, source: str) -> str:
    canonical = json.dumps(
        {"entries": sorted(entries), "reason": reason, "source": source},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


class InMemoryEconomyLedger:
    """Atomic in-memory ledger adapter; production persistence uses Mongo transactions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._balances: dict[tuple[str, str], int] = {}
        self._transactions: list[LedgerTransaction] = []
        self._idempotency: dict[tuple[str, str, str, str], tuple[str, LedgerTransaction]] = {}

    def balance(self, account_id: str, asset_id: str) -> int:
        with self._lock:
            return self._balances.get((account_id, asset_id), 0)

    def transactions(self) -> tuple[LedgerTransaction, ...]:
        with self._lock:
            return tuple(self._transactions)

    def post(
        self,
        *,
        studio_id: str,
        game_id: str,
        player_id: str,
        idempotency_key: str,
        entries: Iterable[tuple[str, str, int]],
        reason: str,
        source: str,
        actor_id: str,
        definition_digest: str,
        compensates_transaction_id: str | None = None,
    ) -> LedgerTransaction:
        lines = tuple(entries)
        if not idempotency_key or not reason or not source:
            raise EconomyError("ledger_metadata_required")
        if len(lines) < 2:
            raise EconomyError("ledger_requires_double_entry")
        grouped: dict[tuple[str, str], int] = {}
        for account_id, asset_id, amount in lines:
            if (
                not account_id
                or not asset_id
                or isinstance(amount, bool)
                or not isinstance(amount, int)
            ):
                raise EconomyError("invalid_ledger_entry")
            if amount < INT64_MIN or amount > INT64_MAX:
                raise EconomyError("amount_overflow")
            if account_id.startswith("system_") and account_id not in SYSTEM_ACCOUNTS:
                raise EconomyError("unknown_system_account")
            grouped[(account_id, asset_id)] = grouped.get((account_id, asset_id), 0) + amount
            if (
                grouped[(account_id, asset_id)] < INT64_MIN
                or grouped[(account_id, asset_id)] > INT64_MAX
            ):
                raise EconomyError("amount_overflow")
        if len(grouped) < 2:
            raise EconomyError("ledger_requires_distinct_accounts")
        assets = {asset for _, asset in grouped}
        if any(
            sum(amount for (_, asset), amount in grouped.items() if asset == target) != 0
            for target in assets
        ):
            raise EconomyError("ledger_unbalanced")
        identity = (studio_id, game_id, player_id, idempotency_key)
        fingerprint = _fingerprint(
            ((account, asset, amount) for (account, asset), amount in grouped.items()),
            reason,
            source,
        )
        with self._lock:
            previous = self._idempotency.get(identity)
            if previous is not None:
                if previous[0] != fingerprint:
                    raise EconomyError("idempotency_conflict")
                return previous[1]
            updated: dict[tuple[str, str], int] = {}
            result_entries: list[LedgerEntry] = []
            for (account_id, asset_id), amount in sorted(grouped.items()):
                key = (account_id, asset_id)
                balance = self._balances.get(key, 0) + amount
                if balance < INT64_MIN or balance > INT64_MAX:
                    raise EconomyError("balance_overflow")
                if not account_id.startswith("system_") and balance < 0:
                    raise EconomyError("insufficient_balance")
                updated[key] = balance
                result_entries.append(
                    LedgerEntry(new_uuid7(), account_id, asset_id, amount, balance)
                )
            transaction = LedgerTransaction(
                new_uuid7(),
                studio_id,
                game_id,
                player_id,
                idempotency_key,
                reason,
                source,
                actor_id,
                definition_digest,
                tuple(result_entries),
                datetime.now(UTC),
                compensates_transaction_id,
            )
            self._balances.update(updated)
            self._transactions.append(transaction)
            self._idempotency[identity] = (fingerprint, transaction)
            return transaction

    def compensate(
        self,
        transaction_id: str,
        *,
        idempotency_key: str,
        actor_id: str,
    ) -> LedgerTransaction:
        with self._lock:
            original = next(
                (item for item in self._transactions if item.transaction_id == transaction_id), None
            )
        if original is None:
            raise EconomyError("transaction_not_found")
        return self.post(
            studio_id=original.studio_id,
            game_id=original.game_id,
            player_id=original.player_id,
            idempotency_key=idempotency_key,
            entries=(
                (entry.account_id, entry.asset_id, -entry.amount) for entry in original.entries
            ),
            reason="compensation",
            source="compensation",
            actor_id=actor_id,
            definition_digest=original.definition_digest,
            compensates_transaction_id=original.transaction_id,
        )

    def reconcile(self) -> Mapping[str, int]:
        """Rebuild projection from immutable entries and fail on any divergence."""
        rebuilt: dict[tuple[str, str], int] = {}
        for transaction in self.transactions():
            for entry in transaction.entries:
                key = (entry.account_id, entry.asset_id)
                rebuilt[key] = rebuilt.get(key, 0) + entry.amount
        with self._lock:
            if rebuilt != self._balances:
                raise EconomyError("balance_projection_mismatch")
            return {
                f"{account}:{asset}": value for (account, asset), value in sorted(rebuilt.items())
            }


class InMemoryEconomyActionService:
    """Atomic receipt/ledger/idempotency/outbox facade for offline and fault tests."""

    def __init__(self, ledger: InMemoryEconomyLedger | None = None) -> None:
        self.ledger = ledger or InMemoryEconomyLedger()
        self._lock = threading.RLock()
        self._receipts: dict[tuple[str, str, str, str, str], tuple[str, EconomyActionReceipt]] = {}
        self._outbox: list[Mapping[str, object]] = []

    def execute(
        self,
        *,
        studio_id: str,
        game_id: str,
        player_id: str,
        actor_id: str,
        action_id: str,
        idempotency_key: str,
        action: EconomyAction,
        definition_digest: str,
        fault: Literal["none", "before_commit", "after_commit"] = "none",
    ) -> EconomyActionReceipt:
        if not all(
            (studio_id, game_id, player_id, actor_id, action_id, idempotency_key, definition_digest)
        ):
            raise EconomyError("economy_action_scope_required")
        if fault not in {"none", "before_commit", "after_commit"}:
            raise EconomyError("invalid_fault_injection_point")
        command_digest = hashlib.sha256(
            json.dumps(asdict(action), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        identity = (studio_id, game_id, player_id, actor_id, idempotency_key)
        with self._lock:
            previous = self._receipts.get(identity)
            if previous is not None:
                if previous[0] != command_digest:
                    raise EconomyError("idempotency_conflict")
                return previous[1]
            assets = set(action.costs) | set(action.grants)
            assets.update(target for target, _, _ in action.overflow_routes.values())
            balances = {
                asset: self.ledger.balance(f"player:{player_id}:{asset}", asset) for asset in assets
            }
            entries = plan_economy_entries(action, balances, player_id=player_id)
            if fault == "before_commit":
                raise EconomyError("injected_failure_before_commit")
            transaction = self.ledger.post(
                studio_id=studio_id,
                game_id=game_id,
                player_id=player_id,
                idempotency_key=idempotency_key,
                entries=entries,
                reason=action_id,
                source="player_action",
                actor_id=actor_id,
                definition_digest=definition_digest,
            )
            event_id = new_uuid7()
            changed_assets = sorted({entry.asset_id for entry in transaction.entries})
            projected = {
                asset: self.ledger.balance(f"player:{player_id}:{asset}", asset)
                for asset in changed_assets
            }
            receipt = EconomyActionReceipt(
                new_uuid7(),
                transaction.transaction_id,
                studio_id,
                game_id,
                player_id,
                actor_id,
                action_id,
                idempotency_key,
                "committed",
                projected,
                (event_id,),
                transaction.occurred_at,
            )
            self._receipts[identity] = (command_digest, receipt)
            self._outbox.append(
                {
                    "event_id": event_id,
                    "type": "economy.action_committed.v1",
                    "transaction_id": transaction.transaction_id,
                    "receipt_id": receipt.receipt_id,
                    "studio_id": studio_id,
                    "game_id": game_id,
                    "player_id": player_id,
                    "status": "pending",
                }
            )
            if fault == "after_commit":
                raise OperationStatusUnknown("operation_status_unknown")
            return receipt

    def receipt(
        self, studio_id: str, game_id: str, player_id: str, receipt_id: str
    ) -> EconomyActionReceipt | None:
        with self._lock:
            return next(
                (
                    receipt
                    for key, (_, receipt) in self._receipts.items()
                    if key[:3] == (studio_id, game_id, player_id)
                    and receipt.receipt_id == receipt_id
                ),
                None,
            )

    def outbox(self) -> tuple[Mapping[str, object], ...]:
        with self._lock:
            return tuple(self._outbox)
