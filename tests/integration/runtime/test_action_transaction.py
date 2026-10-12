from datetime import UTC, datetime

import pytest

from packages.domain.actions import ActionReceipt, InMemoryActionRepository
from packages.domain.event_delivery import InMemoryConsumerInbox
from packages.runtime.src.lengeas_runtime.actions import ActionPlan, PlannedOperation
from packages.runtime.src.lengeas_runtime.conditions import Explanation
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.events import InboxKey


def receipt(receipt_id: str = "r1") -> ActionReceipt:
    return ActionReceipt(
        receipt_id,
        "actor",
        "studio",
        "game",
        "player",
        "act_test",
        "input",
        "definition",
        "1.0.0",
        0,
        1,
        "",
        datetime(2030, 1, 1, tzinfo=UTC).isoformat(),
        1,
        "committed",
        {},
        (),
    )


def test_commit_state_receipt_idempotency_and_outbox_are_atomic() -> None:
    store = InMemoryActionRepository()
    key = ("studio", "game", "player")
    store.seed_state(key, {"player": {"coins": 2}})
    plan = ActionPlan(
        "act_test",
        "input",
        True,
        Explanation("all", True, "condition_met"),
        (),
        (PlannedOperation("increment", "core", "player.coins", 3, 0),),
        (),
        (),
        (),
        1,
    )
    committed = store.commit_action(
        state_key=key,
        expected_version=0,
        idempotency_key="idem-1",
        fingerprint="same",
        actor_id="actor",
        plan=plan,
        receipt=receipt(),
        outbox=(),
    )
    assert committed.state_version == 1
    assert store.state(key) == (1, {"player": {"coins": 5}})
    assert store.receipt(("studio", "game", "player"), "r1") == committed
    assert (
        store.commit_action(
            state_key=key,
            expected_version=0,
            idempotency_key="idem-1",
            fingerprint="same",
            actor_id="actor",
            plan=plan,
            receipt=receipt("r2"),
            outbox=(),
        )
        == committed
    )
    assert store.state(key)[0] == 1
    with pytest.raises(RuntimeErrorCode, match="idempotency_conflict"):
        store.commit_action(
            state_key=key,
            expected_version=1,
            idempotency_key="idem-1",
            fingerprint="different",
            actor_id="actor",
            plan=plan,
            receipt=receipt("r3"),
            outbox=(),
        )
    assert store.state(key)[0] == 1


def test_expected_version_conflict_leaves_no_partial_records() -> None:
    store = InMemoryActionRepository()
    key = ("studio", "game", "player")
    store.seed_state(key, {})
    plan = ActionPlan(
        "a", "d", True, Explanation("all", True, "condition_met"), (), (), (), (), (), 0
    )
    with pytest.raises(RuntimeErrorCode, match="state_conflict"):
        store.commit_action(
            state_key=key,
            expected_version=1,
            idempotency_key="idem",
            fingerprint="f",
            actor_id="actor",
            plan=plan,
            receipt=receipt(),
            outbox=(),
        )
    assert not store.receipts and not store.idempotency and not store.outbox


def test_consumer_inbox_deduplicates_delivery_per_consumer() -> None:
    inbox = InMemoryConsumerInbox()
    key = InboxKey("projection", "event-1")
    assert inbox.record_once(key)
    assert not inbox.record_once(key)
    assert inbox.record_once(InboxKey("analytics", "event-1"))
