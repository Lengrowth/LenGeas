"""Cross-domain integrity checks that quarantine and propose, never mutate fixes."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from packages.domain.ids import new_uuid7


@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    finding_id: str
    code: str
    entity_type: str
    entity_id: str
    severity: str
    detail: str
    detected_at: datetime


@dataclass(frozen=True, slots=True)
class RepairProposal:
    proposal_id: str
    finding_id: str
    operation: str
    target_id: str
    details: Mapping[str, Any]
    requires_owner_review: bool = True


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    run_id: str
    checked_at: datetime
    checked_counts: Mapping[str, int]
    findings: tuple[IntegrityFinding, ...]
    repair_proposals: tuple[RepairProposal, ...]


class ReconciliationService:
    """Cross-check snapshots from receipts, ledger, inventory, entitlements and delivery."""

    def __init__(
        self,
        *,
        alert: Callable[[IntegrityFinding], None] | None = None,
        quarantine: Callable[[str, str], None] | None = None,
    ) -> None:
        self._alert = alert or (lambda _finding: None)
        self._quarantine = quarantine or (lambda _type, _id: None)

    def run(
        self,
        *,
        receipts: Sequence[Mapping[str, Any]],
        ledger_transactions: Sequence[Mapping[str, Any]],
        balance_projections: Mapping[tuple[str, str], int],
        inventories: Sequence[Mapping[str, Any]],
        item_history: Sequence[Mapping[str, Any]],
        entitlements: Sequence[Mapping[str, Any]],
        provider_transactions: Sequence[Mapping[str, Any]],
        cross_game_deliveries: Sequence[Mapping[str, Any]],
        approved_contracts: Mapping[str, Mapping[str, Any]],
    ) -> ReconciliationReport:
        findings: list[IntegrityFinding] = []
        proposals: list[RepairProposal] = []
        now = datetime.now(UTC)

        def report(
            code: str,
            entity_type: str,
            entity_id: str,
            detail: str,
            operation: str,
            **proposal_details: Any,
        ) -> None:
            finding = IntegrityFinding(
                new_uuid7(), code, entity_type, entity_id, "high", detail, now
            )
            findings.append(finding)
            proposals.append(
                RepairProposal(
                    new_uuid7(), finding.finding_id, operation, entity_id, proposal_details
                )
            )
            self._alert(finding)
            self._quarantine(entity_type, entity_id)

        transaction_by_id = {str(item.get("transaction_id")): item for item in ledger_transactions}
        receipt_by_id = {str(item.get("receipt_id")): item for item in receipts}
        for receipt in receipts:
            receipt_id = str(receipt.get("receipt_id", ""))
            transaction_id = receipt.get("ledger_transaction_id")
            if transaction_id and str(transaction_id) not in transaction_by_id:
                report(
                    "receipt_without_ledger",
                    "receipt",
                    receipt_id,
                    "Receipt references a ledger transaction that is missing.",
                    "review_missing_ledger_transaction",
                    transaction_id=transaction_id,
                )

        rebuilt: dict[tuple[str, str], int] = defaultdict(int)
        for transaction in ledger_transactions:
            transaction_id = str(transaction.get("transaction_id", ""))
            entries = transaction.get("entries", [])
            totals: Counter[str] = Counter()
            for entry in entries:
                asset = str(entry.get("asset_id", ""))
                account = str(entry.get("account_id", ""))
                amount = entry.get("amount")
                if not isinstance(amount, int) or isinstance(amount, bool):
                    report(
                        "ledger_amount_invalid",
                        "ledger_transaction",
                        transaction_id,
                        "Ledger entry amount is not an integer.",
                        "quarantine_ledger_transaction",
                    )
                    continue
                totals[asset] += amount
                rebuilt[(account, asset)] += amount
            if len(entries) < 2 or any(value != 0 for value in totals.values()):
                report(
                    "ledger_unbalanced",
                    "ledger_transaction",
                    transaction_id,
                    "Ledger transaction does not conserve value per asset.",
                    "propose_compensating_transaction",
                )
            ledger_receipt_id = transaction.get("receipt_id")
            if ledger_receipt_id and str(ledger_receipt_id) not in receipt_by_id:
                report(
                    "ledger_without_receipt",
                    "ledger_transaction",
                    transaction_id,
                    "Ledger transaction references a missing receipt.",
                    "review_orphan_ledger_transaction",
                    receipt_id=ledger_receipt_id,
                )
        if dict(rebuilt) != dict(balance_projections):
            for account, asset in sorted(set(rebuilt) | set(balance_projections)):
                if rebuilt.get((account, asset), 0) != balance_projections.get((account, asset), 0):
                    report(
                        "balance_projection_mismatch",
                        "balance_projection",
                        f"{account}:{asset}",
                        "Balance projection differs from the append-only ledger.",
                        "rebuild_balance_projection",
                        expected=rebuilt.get((account, asset), 0),
                    )

        history_totals: Counter[tuple[str, str, str]] = Counter()
        instance_history: Counter[tuple[str, str]] = Counter()
        for record in item_history:
            scope = str(
                record.get("scope_id")
                or ":".join(
                    str(record.get(key, ""))
                    for key in ("studio_id", "game_id", "player_id", "container_id")
                )
            )
            item_id = str(record.get("item_id", ""))
            operation = record.get("operation")
            amount = record.get("quantity", 0)
            if not isinstance(amount, int) or isinstance(amount, bool):
                report(
                    "item_history_quantity_invalid",
                    "item_history",
                    str(record.get("history_id", "")),
                    "History quantity is not an integer.",
                    "rebuild_inventory_history",
                )
                continue
            if operation in {"grant", "transfer_in"}:
                history_totals[(scope, item_id, "quantity")] += amount
                for instance_id in record.get("instance_ids", []):
                    instance_history[(scope, str(instance_id))] += 1
            elif operation in {"consume", "transfer_out"}:
                history_totals[(scope, item_id, "quantity")] -= amount
                for instance_id in record.get("instance_ids", []):
                    instance_history[(scope, str(instance_id))] -= 1
        for inventory in inventories:
            inventory_id = str(inventory.get("inventory_id") or inventory.get("container_id", ""))
            scope = str(
                inventory.get("scope_id")
                or ":".join(
                    str(inventory.get(key, ""))
                    for key in ("studio_id", "game_id", "player_id", "container_id")
                )
            )
            actual: Counter[tuple[str, str, str]] = Counter()
            actual_instances: set[str] = set()
            capacity = inventory.get("capacity_slots")
            version = inventory.get("state_version")
            if (
                not isinstance(capacity, int)
                or isinstance(capacity, bool)
                or capacity < 0
                or not isinstance(version, int)
                or isinstance(version, bool)
                or version < 0
            ):
                report(
                    "inventory_metadata_invalid",
                    "inventory",
                    inventory_id,
                    "Inventory capacity or optimistic state version is invalid.",
                    "review_inventory_metadata",
                )
            for stack in inventory.get("stacks", []):
                quantity = stack.get("quantity")
                if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
                    report(
                        "inventory_stack_quantity_invalid",
                        "inventory",
                        inventory_id,
                        "Inventory stack has an invalid quantity.",
                        "review_inventory_stack",
                    )
                    continue
                actual[(scope, str(stack.get("item_id", "")), "quantity")] += quantity
            for item in inventory.get("instances", []):
                actual[(scope, str(item.get("item_id", "")), "quantity")] += 1
                instance_id = str(item.get("instance_id", ""))
                if not instance_id or instance_id in actual_instances:
                    report(
                        "inventory_instance_identity_invalid",
                        "inventory",
                        inventory_id,
                        "Inventory has an empty or duplicate unique instance ID.",
                        "review_unique_item_identity",
                    )
                actual_instances.add(instance_id)
            occupied_slots = len(inventory.get("stacks", [])) + len(inventory.get("instances", []))
            if isinstance(capacity, int) and occupied_slots > capacity:
                report(
                    "inventory_capacity_exceeded",
                    "inventory",
                    inventory_id,
                    "Inventory occupies more slots than its configured capacity.",
                    "review_inventory_capacity",
                    occupied_slots=occupied_slots,
                    capacity=capacity,
                )
            equipment = inventory.get("equipment", {})
            if (
                isinstance(equipment, Mapping)
                and set(map(str, equipment.values())) - actual_instances
            ):
                report(
                    "inventory_equipment_reference_invalid",
                    "inventory",
                    inventory_id,
                    "Equipment references a unique item that is not in the container.",
                    "review_equipment_reference",
                )
            expected_items = {
                key: value for key, value in history_totals.items() if key[0] == scope
            }
            actual_items = {key: value for key, value in actual.items() if value}
            # Consumption history may include initial grants outside the retained window.
            if expected_items != actual_items:
                report(
                    "inventory_history_mismatch",
                    "inventory",
                    inventory_id,
                    "Current inventory does not match its recorded item history.",
                    "rebuild_item_history",
                    history=dict(expected_items),
                    actual=dict(actual_items),
                )
            expected_instances = {
                instance_id
                for (instance_scope, instance_id), count in instance_history.items()
                if instance_scope == scope and count == 1
            }
            if expected_instances != actual_instances:
                report(
                    "inventory_instance_history_mismatch",
                    "inventory",
                    inventory_id,
                    "Current unique instance IDs differ from immutable item history.",
                    "rebuild_unique_item_history",
                    expected=sorted(expected_instances),
                    actual=sorted(actual_instances),
                )

        provider_ids: Counter[tuple[str, str]] = Counter(
            (str(item.get("provider", "")), str(item.get("provider_transaction_id", "")))
            for item in provider_transactions
        )
        for key, count in provider_ids.items():
            if count > 1:
                report(
                    "provider_transaction_duplicate",
                    "provider_transaction",
                    ":".join(key),
                    "Provider transaction ID appears more than once.",
                    "quarantine_duplicate_purchase",
                )
        provider_set = set(provider_ids)
        for entitlement in entitlements:
            if entitlement.get("status") == "active":
                key = (
                    str(entitlement.get("provider", "")),
                    str(entitlement.get("provider_transaction_id", "")),
                )
                if key not in provider_set:
                    report(
                        "entitlement_without_purchase",
                        "entitlement",
                        str(entitlement.get("entitlement_id", "")),
                        "Active entitlement has no verified provider transaction.",
                        "revoke_unbacked_entitlement",
                    )

        delivery_ids: Counter[tuple[str, str]] = Counter(
            (str(item.get("contract_id", "")), str(item.get("source_event_id", "")))
            for item in cross_game_deliveries
        )
        for key, count in delivery_ids.items():
            if count > 1:
                report(
                    "cross_game_delivery_duplicate",
                    "cross_game_delivery",
                    ":".join(key),
                    "Source event has duplicate delivery records.",
                    "quarantine_duplicate_delivery",
                )
        for delivery in cross_game_deliveries:
            contract_id = str(delivery.get("contract_id", ""))
            contract = approved_contracts.get(contract_id)
            if contract is None or contract.get("status") != "approved":
                report(
                    "cross_game_delivery_unapproved",
                    "cross_game_delivery",
                    str(delivery.get("delivery_id", "")),
                    "Delivery has no currently approved contract.",
                    "review_cross_game_delivery",
                )

        return ReconciliationReport(
            new_uuid7(),
            now,
            {
                "receipts": len(receipts),
                "ledger_transactions": len(ledger_transactions),
                "inventories": len(inventories),
                "entitlements": len(entitlements),
                "cross_game_deliveries": len(cross_game_deliveries),
            },
            tuple(findings),
            tuple(proposals),
        )
