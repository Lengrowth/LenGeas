from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from packages.domain.cross_game import (
    CrossGameContract,
    CrossGameError,
    InMemoryCrossGameService,
    SourceEvent,
)
from packages.domain.entitlements import (
    EntitlementError,
    InMemoryEntitlementRepository,
    VerifiedPurchase,
)
from packages.domain.reconciliation import ReconciliationService


def _purchase(
    *, provider_id: str = "txn-1", expires_at: datetime | None = None
) -> VerifiedPurchase:
    return VerifiedPurchase(
        "apple",
        provider_id,
        "coins",
        "player",
        "game",
        "studio",
        datetime.now(UTC),
        expires_at,
        "sandbox",
    )


def test_permanent_provider_transaction_id_prevents_duplicate_grants_and_refund_replay() -> None:
    repository = InMemoryEntitlementRepository()
    receipt, entitlement = repository.fulfill(
        _purchase(), kind="consumable", quantity=3, idempotency_key="claim"
    )
    duplicate, same_entitlement = repository.fulfill(
        _purchase(), kind="consumable", quantity=3, idempotency_key="different-request-key"
    )
    assert duplicate == receipt
    assert same_entitlement == entitlement
    with pytest.raises(EntitlementError, match="provider_transaction_conflict"):
        repository.fulfill(_purchase(), kind="permanent", idempotency_key="replay")
    consumed = repository.consume(entitlement.entitlement_id, 2)
    assert consumed.quantity_remaining == 1
    revoked = repository.revoke("apple", "txn-1", reason="refund")
    assert revoked.status == "revoked"
    assert repository.revoke("apple", "txn-1", reason="refund") == revoked
    assert repository.entitlements("studio", "game", "player") == ()


def test_subscription_entitlements_expire_and_refunds_do_not_delete_history() -> None:
    repository = InMemoryEntitlementRepository()
    expiry = datetime.now(UTC) + timedelta(minutes=1)
    receipt, entitlement = repository.fulfill(
        _purchase(expires_at=expiry), kind="subscription", idempotency_key="subscription"
    )
    expired = repository.expire_due(expiry + timedelta(seconds=1))
    assert expired == (repository.all_entitlements()[0],)
    assert expired[0].status == "expired"
    assert receipt.entitlement_id == entitlement.entitlement_id


def test_webhook_duplicate_is_idempotent_but_changed_payload_is_rejected() -> None:
    repository = InMemoryEntitlementRepository()
    assert repository.accept_webhook("google", "msg-1", "digest-a")
    assert not repository.accept_webhook("google", "msg-1", "digest-a")
    with pytest.raises(EntitlementError, match="webhook_replay_conflict"):
        repository.accept_webhook("google", "msg-1", "digest-b")


def test_cross_game_approved_delivery_is_bounded_idempotent_and_revocable() -> None:
    service = InMemoryCrossGameService()
    contract = CrossGameContract(
        "contract-1",
        "studio",
        "game-a",
        "game-b",
        frozenset({"quest.completed.v1"}),
        "grant_welcome",
        frozenset({"coins"}),
        {"coins": 100},
        1,
        "approved",
    )
    service.approve(contract)
    event = SourceEvent(
        "event-1",
        "quest.completed.v1",
        "studio",
        "game-a",
        "player",
        {"coins": 40},
        "sha256:definition",
        datetime.now(UTC),
    )
    target_calls = []

    def target_action(game_id, action_id, payload):
        target_calls.append((game_id, action_id, dict(payload)))
        return {"applied": True}

    first = service.deliver("contract-1", event, "target-player", target_action=target_action)
    assert (
        service.deliver("contract-1", event, "target-player", target_action=target_action) == first
    )
    assert len(target_calls) == 1
    next_event = SourceEvent(
        "event-2",
        "quest.completed.v1",
        "studio",
        "game-a",
        "player",
        {"coins": 1},
        "sha256:definition",
        datetime.now(UTC),
    )
    with pytest.raises(CrossGameError, match="delivery_limit_exceeded"):
        service.deliver("contract-1", next_event, "target-player", target_action=target_action)
    service.revoke("contract-1")
    with pytest.raises(CrossGameError, match="contract_not_approved"):
        service.deliver("contract-1", next_event, "target-player", target_action=target_action)


def test_cross_game_rejects_cycles_unapproved_source_payload_and_reward_overflow() -> None:
    service = InMemoryCrossGameService()

    def contract(contract_id, source, target):
        return CrossGameContract(
            contract_id,
            "studio",
            source,
            target,
            frozenset({"event.v1"}),
            "apply_reward",
            frozenset({"coins"}),
            {"coins": 10},
            5,
            "approved",
        )

    service.approve(contract("ab", "a", "b"))
    with pytest.raises(CrossGameError, match="cross_game_reward_cycle"):
        service.approve(contract("ba", "b", "a"))
    event = SourceEvent("e", "event.v1", "studio", "a", "p", {"coins": 11}, "d", datetime.now(UTC))
    with pytest.raises(CrossGameError, match="delivery_reward_limit_exceeded"):
        service.deliver("ab", event, "p2", target_action=lambda *_args: {"ok": True})
    wrong_source = SourceEvent(
        "bad", "event.v1", "studio", "b", "p", {"coins": 2}, "d", datetime.now(UTC)
    )
    with pytest.raises(CrossGameError, match="source_event_not_authorized"):
        service.deliver("ab", wrong_source, "p2", target_action=lambda *_args: {"ok": True})


def test_reconciliation_alerts_quarantines_and_proposes_repair_without_mutating() -> None:
    alerts = []
    quarantined = []
    service = ReconciliationService(
        alert=alerts.append,
        quarantine=lambda entity_type, entity_id: quarantined.append((entity_type, entity_id)),
    )
    report = service.run(
        receipts=[{"receipt_id": "receipt-1", "ledger_transaction_id": "missing-tx"}],
        ledger_transactions=[
            {
                "transaction_id": "bad-tx",
                "entries": [
                    {"account_id": "player:p:coin", "asset_id": "coin", "amount": 5},
                    {"account_id": "system_faucet", "asset_id": "coin", "amount": -4},
                ],
            }
        ],
        balance_projections={("player:p:coin", "coin"): 4},
        inventories=[],
        item_history=[],
        entitlements=[
            {
                "entitlement_id": "ent-1",
                "provider": "apple",
                "provider_transaction_id": "missing",
                "status": "active",
            }
        ],
        provider_transactions=[],
        cross_game_deliveries=[],
        approved_contracts={},
    )
    assert {item.code for item in report.findings} >= {
        "receipt_without_ledger",
        "ledger_unbalanced",
        "entitlement_without_purchase",
    }
    assert len(alerts) == len(report.findings)
    assert len(quarantined) == len(report.findings)
    assert all(proposal.requires_owner_review for proposal in report.repair_proposals)


def test_reconciliation_detects_inventory_without_history_and_unique_id_divergence() -> None:
    report = ReconciliationService().run(
        receipts=[],
        ledger_transactions=[],
        balance_projections={},
        inventories=[
            {
                "studio_id": "s",
                "game_id": "g",
                "player_id": "p",
                "container_id": "bag",
                "capacity_slots": 2,
                "state_version": 1,
                "instances": [{"instance_id": "heirloom-1", "item_id": "heirloom"}],
                "stacks": [],
                "equipment": {},
            }
        ],
        item_history=[],
        entitlements=[],
        provider_transactions=[],
        cross_game_deliveries=[],
        approved_contracts={},
    )
    assert {finding.code for finding in report.findings} == {
        "inventory_history_mismatch",
        "inventory_instance_history_mismatch",
    }
