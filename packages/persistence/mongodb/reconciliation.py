"""Reconciliation snapshots, quarantine alerts, and review-only repair proposals."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from packages.domain.ids import new_uuid7
from packages.domain.reconciliation import ReconciliationReport, ReconciliationService


class MongoReconciliationRepository:
    """Reads documented collections and persists findings without auto-repairing value."""

    def __init__(self, database: Any) -> None:
        self.database = database
        self.service = ReconciliationService()

    async def _all(self, collection: Any, query: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [document async for document in collection.find(dict(query))]

    async def run(self, *, studio_id: str | None = None) -> ReconciliationReport:
        scope = {"studio_id": studio_id} if studio_id else {}
        receipts = await self._all(self.database.action_receipts, scope)
        ledger_all = await self._all(self.database.economy_ledger, scope)
        transactions = [item for item in ledger_all if item.get("record_type") == "transaction"]
        projections = {
            (str(item.get("account_id", "")), str(item.get("asset_id", ""))): int(
                item.get("balance", 0)
            )
            for item in ledger_all
            if item.get("record_type") == "balance_projection"
        }
        inventories = await self._all(self.database.inventories, scope)
        history = await self._all(
            self.database.audit_logs, {**scope, "event_type": "inventory.item_history.v1"}
        )
        entitlements = await self._all(self.database.entitlements, scope)
        provider_transactions = await self._all(
            self.database.idempotency_records,
            {"provider_transaction_id": {"$type": "string"}, **scope},
        )
        deliveries = await self._all(
            self.database.action_receipts, {**scope, "record_type": "cross_game_delivery"}
        )
        blueprints = await self._all(self.database.game_blueprints, scope)
        contracts = {
            str(contract.get("contract_id")): contract
            for blueprint in blueprints
            for contract in blueprint.get("cross_game_contracts", [])
        }
        # Runtime receipts share action_receipts with purchase receipts. Only include
        # fields that refer to a ledger transaction when comparing ledger coverage.
        actionable_receipts = [
            item
            for item in receipts
            if item.get("transaction_id") and item.get("record_type") != "cross_game_delivery"
        ]
        report = self.service.run(
            receipts=[
                {**item, "ledger_transaction_id": item.get("transaction_id")}
                for item in actionable_receipts
            ],
            ledger_transactions=transactions,
            balance_projections=projections,
            inventories=inventories,
            item_history=history,
            entitlements=entitlements,
            provider_transactions=provider_transactions,
            cross_game_deliveries=deliveries,
            approved_contracts=contracts,
        )
        await self._persist(report)
        return report

    async def _persist(self, report: ReconciliationReport) -> None:
        async with await self.database.client.start_session() as session:
            async with session.start_transaction():
                for finding in report.findings:
                    now = datetime.now(UTC)
                    await self.database.audit_logs.insert_one(
                        {
                            "audit_id": new_uuid7(),
                            "event_type": "integrity.finding.v1",
                            "finding_id": finding.finding_id,
                            "code": finding.code,
                            "entity_type": finding.entity_type,
                            "entity_id": finding.entity_id,
                            "severity": finding.severity,
                            "detail": finding.detail,
                            "quarantined": True,
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    await self.database.outbox_events.insert_one(
                        {
                            "event_id": new_uuid7(),
                            "event_type": "integrity.alert.v1",
                            "finding_id": finding.finding_id,
                            "entity_type": finding.entity_type,
                            "entity_id": finding.entity_id,
                            "severity": finding.severity,
                            "status": "pending",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    await self._quarantine(finding.entity_type, finding.entity_id, session)
                for proposal in report.repair_proposals:
                    await self.database.audit_logs.insert_one(
                        {
                            "audit_id": new_uuid7(),
                            "event_type": "reconciliation.repair_proposed.v1",
                            "proposal_id": proposal.proposal_id,
                            "finding_id": proposal.finding_id,
                            "operation": proposal.operation,
                            "target_id": proposal.target_id,
                            "details": dict(proposal.details),
                            "status": "requires_owner_review",
                            "occurred_at": datetime.now(UTC),
                        },
                        session=session,
                    )

    async def _quarantine(self, entity_type: str, entity_id: str, session: Any) -> None:
        if entity_type == "receipt":
            await self.database.action_receipts.update_one(
                {"receipt_id": entity_id}, {"$set": {"quarantined": True}}, session=session
            )
        elif entity_type == "ledger_transaction":
            # The immutable ledger is never edited; its audit finding carries
            # the quarantine marker and the related projection is frozen.
            return
        elif entity_type == "balance_projection":
            account, _, asset = entity_id.rpartition(":")
            await self.database.economy_ledger.update_many(
                {"record_type": "balance_projection", "account_id": account, "asset_id": asset},
                {"$set": {"quarantined": True}},
                session=session,
            )
        elif entity_type == "inventory":
            await self.database.inventories.update_one(
                {"container_id": entity_id}, {"$set": {"quarantined": True}}, session=session
            )
        elif entity_type == "item_history":
            await self.database.audit_logs.update_one(
                {"audit_id": entity_id, "event_type": "inventory.item_history.v1"},
                {"$set": {"quarantined": True}},
                session=session,
            )
        elif entity_type == "entitlement":
            await self.database.entitlements.update_one(
                {"entitlement_id": entity_id}, {"$set": {"quarantined": True}}, session=session
            )
        elif entity_type == "cross_game_delivery":
            await self.database.action_receipts.update_one(
                {"record_type": "cross_game_delivery", "delivery_id": entity_id},
                {"$set": {"quarantined": True}},
                session=session,
            )
        elif entity_type == "provider_transaction":
            provider, _, transaction_id = entity_id.partition(":")
            await self.database.idempotency_records.update_one(
                {"provider": provider, "provider_transaction_id": transaction_id},
                {"$set": {"quarantined": True}},
                session=session,
            )
