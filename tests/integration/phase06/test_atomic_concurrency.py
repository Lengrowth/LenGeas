from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from packages.domain.economy import (
    EconomyAction,
    EconomyError,
    InMemoryEconomyActionService,
    OperationStatusUnknown,
)


def test_concurrent_duplicate_claim_commits_one_receipt_transaction_and_outbox() -> None:
    service = InMemoryEconomyActionService()
    args = dict(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="daily_claim",
        idempotency_key="daily:2026-10-12",
        definition_digest="d",
        action=EconomyAction(grants={"coin": 25}),
    )
    with ThreadPoolExecutor(max_workers=24) as executor:
        results = list(executor.map(lambda _: service.execute(**args), range(100)))
    assert all(result == results[0] for result in results)
    assert service.ledger.balance("player:p:coin", "coin") == 25
    assert len(service.ledger.transactions()) == 1
    assert len(service.outbox()) == 1


def test_concurrent_spends_cannot_overdraw_shared_balance() -> None:
    service = InMemoryEconomyActionService()
    service.execute(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="seed",
        idempotency_key="seed",
        definition_digest="d",
        action=EconomyAction(grants={"coin": 10}),
    )

    def spend(number: int) -> str:
        try:
            service.execute(
                studio_id="s",
                game_id="g",
                player_id="p",
                actor_id="a",
                action_id="purchase",
                idempotency_key=f"spend:{number}",
                definition_digest="d",
                action=EconomyAction(costs={"coin": 1}),
            )
            return "committed"
        except EconomyError as error:
            assert error.args[0] == "insufficient_balance"
            return "rejected"

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(spend, range(20)))
    assert results.count("committed") == 10
    assert results.count("rejected") == 10
    assert service.ledger.balance("player:p:coin", "coin") == 0
    assert service.ledger.reconcile()["player:p:coin:coin"] == 0


def test_failure_before_commit_is_clean_and_unknown_after_commit_replays_receipt() -> None:
    service = InMemoryEconomyActionService()
    args = dict(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="reward",
        definition_digest="d",
        action=EconomyAction(grants={"coin": 3}),
    )
    with pytest.raises(EconomyError, match="injected_failure_before_commit"):
        service.execute(**args, idempotency_key="before", fault="before_commit")
    assert service.ledger.transactions() == ()
    with pytest.raises(OperationStatusUnknown):
        service.execute(**args, idempotency_key="after", fault="after_commit")
    receipt = service.execute(**args, idempotency_key="after")
    assert receipt.status == "committed"
    assert len(service.ledger.transactions()) == 1
    assert len(service.outbox()) == 1
