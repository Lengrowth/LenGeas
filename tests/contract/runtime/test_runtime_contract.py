from packages.runtime.src.lengeas_runtime.actions import PlannedOperation
from packages.runtime.src.lengeas_runtime.events import InboxKey
from packages.runtime.src.lengeas_runtime.registry import core_registry


def test_core_registry_covers_schema_effect_and_reward_names() -> None:
    registry = core_registry()
    for effect in (
        "set",
        "increment",
        "decrement",
        "append_unique",
        "remove",
        "unlock",
        "lock",
        "grant_item",
        "consume_item",
        "equip",
        "unequip",
        "apply_modifier",
        "remove_modifier",
        "start_timer",
        "cancel_timer",
        "complete_objective",
        "emit_event",
    ):
        assert registry.effect(effect, "core", {}, {"operation": effect})
    for reward in (
        "resource",
        "item",
        "unlock",
        "entitlement",
        "progression",
        "cosmetic",
        "loot_table",
        "cross_game_contract",
    ):
        assert registry.reward(reward, "core", {"type": reward})
    assert InboxKey("projection", "event-1").consumer == "projection"


def test_plan_operations_are_immutable_and_ordered() -> None:
    op = PlannedOperation("set", "core", "player.level", 2, 0)
    assert op.ordinal == 0
    try:
        op.value = 3  # type: ignore[misc]
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("planned operations must be immutable")
