from __future__ import annotations

import asyncio

import pytest

from packages.domain.economy import (
    EconomyAction,
    EconomyError,
    InMemoryEconomyActionService,
    InMemoryEconomyLedger,
    OperationStatusUnknown,
)
from packages.domain.inventory import (
    InMemoryInventoryRepository,
    InventoryError,
    InventoryScope,
    ItemDefinition,
)
from packages.domain.player_state import (
    InMemoryPlayerStateRepository,
    PlayerStateScope,
    StateError,
)


def test_player_state_is_partitioned_versioned_and_returns_patch() -> None:
    repository = InMemoryPlayerStateRepository()
    scope = PlayerStateScope("studio", "game", "player", "profile")
    other_player = PlayerStateScope("studio", "game", "other", "other-profile")
    first = asyncio.run(repository.patch(scope, "progress", 0, {"level": 1, "xp": 20}))
    assert first.prior_state_version == 0
    assert first.state_version == 1
    assert first.patch == {"level": 1, "xp": 20}
    second = asyncio.run(repository.patch(scope, "progress", 1, {"xp": 25}))
    assert second.prior_state_version == 1
    assert asyncio.run(repository.read(scope, "progress")).data == {"level": 1, "xp": 25}
    assert asyncio.run(repository.read(other_player, "progress")) is None


def test_player_state_rejects_stale_versions_and_oversized_patches() -> None:
    repository = InMemoryPlayerStateRepository()
    scope = PlayerStateScope("studio", "game", "player", "profile")
    asyncio.run(repository.patch(scope, "inventory", 0, {"coins": 1}))
    with pytest.raises(StateError, match="state_conflict"):
        asyncio.run(repository.patch(scope, "inventory", 0, {"coins": 2}))
    with pytest.raises(StateError, match="state_patch_too_large"):
        asyncio.run(repository.patch(scope, "inventory", 1, {"data": "x" * 300_000}))


def test_ledger_conserves_value_and_compensates_without_rewriting_history() -> None:
    ledger = InMemoryEconomyLedger()
    initial = ledger.post(
        studio_id="s",
        game_id="g",
        player_id="p",
        idempotency_key="grant-1",
        entries=(("system_faucet", "coin", -40), ("player:p:coin", "coin", 40)),
        reason="quest_reward",
        source="action",
        actor_id="a",
        definition_digest="sha256:x",
    )
    assert ledger.balance("player:p:coin", "coin") == 40
    correction = ledger.compensate(
        initial.transaction_id, idempotency_key="comp-1", actor_id="admin"
    )
    assert correction.compensates_transaction_id == initial.transaction_id
    assert ledger.balance("player:p:coin", "coin") == 0
    assert len(ledger.transactions()) == 2
    assert ledger.reconcile()["player:p:coin:coin"] == 0


def test_ledger_rejects_unbalanced_negative_and_overflow_entries() -> None:
    ledger = InMemoryEconomyLedger()
    params = dict(
        studio_id="s",
        game_id="g",
        player_id="p",
        reason="test",
        source="test",
        actor_id="a",
        definition_digest="d",
    )
    with pytest.raises(EconomyError, match="ledger_unbalanced"):
        ledger.post(
            idempotency_key="bad",
            entries=(("player:p:coin", "coin", 2), ("system_faucet", "coin", -1)),
            **params,
        )
    with pytest.raises(EconomyError, match="insufficient_balance"):
        ledger.post(
            idempotency_key="negative",
            entries=(("player:p:coin", "coin", -1), ("system_sink", "coin", 1)),
            **params,
        )
    with pytest.raises(EconomyError, match="amount_overflow"):
        ledger.post(
            idempotency_key="overflow",
            entries=(("player:p:coin", "coin", 2**63), ("system_faucet", "coin", -(2**63))),
            **params,
        )


def test_economy_action_is_idempotent_and_handles_commit_uncertainty() -> None:
    service = InMemoryEconomyActionService()
    args = dict(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="claim",
        idempotency_key="key",
        definition_digest="d",
        action=EconomyAction(grants={"coin": 10}),
    )
    first = service.execute(**args)
    assert service.execute(**args) == first
    assert first.balances["coin"] == 10
    assert len(service.outbox()) == 1
    with pytest.raises(OperationStatusUnknown):
        service.execute(**{**args, "idempotency_key": "uncertain"}, fault="after_commit")
    retry = service.execute(**{**args, "idempotency_key": "uncertain"})
    assert retry.status == "committed"
    assert retry.balances["coin"] == 20
    assert len(service.outbox()) == 2


def test_economy_cost_caps_overflow_routes_and_exchange_value() -> None:
    service = InMemoryEconomyActionService()
    service.execute(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="seed",
        idempotency_key="seed",
        definition_digest="d",
        action=EconomyAction(grants={"coin": 100}),
    )
    clamped = service.execute(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="earn",
        idempotency_key="clamp",
        definition_digest="d",
        action=EconomyAction(
            costs={"coin": 10}, grants={"coin": 20}, caps={"coin": 100}, overflow_policy="clamp"
        ),
    )
    assert clamped.balances["coin"] == 100
    routed = service.execute(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="route",
        idempotency_key="route",
        definition_digest="d",
        action=EconomyAction(
            grants={"coin": 10},
            caps={"coin": 100},
            overflow_policy="route",
            overflow_routes={"coin": ("gem", 1, 2)},
        ),
    )
    assert routed.balances["coin"] == 100
    assert routed.balances["gem"] == 5
    assert service.ledger.reconcile()


def test_inventory_stacks_unique_items_equipment_capacity_and_history() -> None:
    repo = InMemoryInventoryRepository()
    scope = InventoryScope("s", "g", "p", "profile", "backpack")
    repo.create(scope, 3)
    stackable = ItemDefinition("potion", True, max_stack=5)
    snapshot = repo.grant(scope, stackable, 7, expected_version=0, idempotency_key="grant")
    assert [stack.quantity for stack in snapshot.stacks] == [5, 2]
    assert repo.grant(scope, stackable, 7, expected_version=0, idempotency_key="grant") == snapshot
    snapshot = repo.consume(scope, "potion", 3, expected_version=1, idempotency_key="consume")
    assert sum(stack.quantity for stack in snapshot.stacks) == 4
    unique = ItemDefinition(
        "sword", False, transferable=True, equipment_slots=frozenset({"main_hand"})
    )
    snapshot = repo.grant(scope, unique, 1, expected_version=2, idempotency_key="sword")
    instance_id = snapshot.instances[0].instance_id
    snapshot = repo.equip(
        scope, instance_id, "main_hand", unique, expected_version=3, idempotency_key="equip"
    )
    assert snapshot.equipment["main_hand"] == instance_id
    assert len(repo.history(scope)) == 4


def test_inventory_denies_capacity_transfer_scope_and_stale_consume() -> None:
    repo = InMemoryInventoryRepository()
    source = InventoryScope("s", "g", "p1", "profile1", "bag")
    target = InventoryScope("s", "g", "p2", "profile2", "bag")
    repo.create(source, 1)
    repo.create(target, 0)
    item = ItemDefinition("stone", True, max_stack=2, transferable=True)
    repo.grant(source, item, 2, expected_version=0, idempotency_key="grant")
    with pytest.raises(InventoryError, match="inventory_capacity_exceeded"):
        repo.transfer(
            source,
            target,
            "stone",
            1,
            item,
            source_version=1,
            target_version=0,
            idempotency_key="move",
        )
    other_game = InventoryScope("s", "g2", "p2", "profile2", "bag")
    repo.create(other_game, 4)
    with pytest.raises(InventoryError, match="cross_game_transfer_denied"):
        repo.transfer(
            source,
            other_game,
            "stone",
            1,
            item,
            source_version=1,
            target_version=0,
            idempotency_key="cross",
        )
    with pytest.raises(InventoryError, match="inventory_conflict"):
        repo.consume(source, "stone", 1, expected_version=0, idempotency_key="stale")


def test_unique_instance_transfer_preserves_identity_and_replay() -> None:
    repo = InMemoryInventoryRepository()
    source = InventoryScope("s", "g", "p1", "profile1", "bag")
    target = InventoryScope("s", "g", "p2", "profile2", "bag")
    repo.create(source, 2)
    repo.create(target, 2)
    definition = ItemDefinition("heirloom", False, transferable=True)
    original = repo.grant(source, definition, 1, expected_version=0, idempotency_key="grant")
    instance_id = original.instances[0].instance_id
    result = repo.transfer(
        source,
        target,
        "heirloom",
        1,
        definition,
        source_version=1,
        target_version=0,
        idempotency_key="transfer",
    )
    assert result[0].instances == ()
    assert result[1].instances[0].instance_id == instance_id
    assert (
        repo.transfer(
            source,
            target,
            "heirloom",
            1,
            definition,
            source_version=1,
            target_version=0,
            idempotency_key="transfer",
        )
        == result
    )


def test_stack_transfer_preserves_attributes_and_requires_idempotency_key() -> None:
    repo = InMemoryInventoryRepository()
    source = InventoryScope("s", "g", "source", "profile1", "bag")
    target = InventoryScope("s", "g", "target", "profile2", "bag")
    repo.create(source, 3)
    repo.create(target, 3)
    definition = ItemDefinition("potion", True, max_stack=5, transferable=True)
    repo.grant(
        source,
        definition,
        4,
        expected_version=0,
        idempotency_key="grant",
        attributes={"quality": "rare"},
    )
    with pytest.raises(InventoryError, match="idempotency_key_required"):
        repo.transfer(
            source,
            target,
            "potion",
            2,
            definition,
            source_version=1,
            target_version=0,
            idempotency_key="",
        )
    source_after, target_after = repo.transfer(
        source,
        target,
        "potion",
        2,
        definition,
        source_version=1,
        target_version=0,
        idempotency_key="move",
    )
    assert source_after.stacks[0].quantity == 2
    assert target_after.stacks[0].quantity == 2
    assert target_after.stacks[0].attributes == {"quality": "rare"}
