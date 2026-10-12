from __future__ import annotations

import pytest

from packages.domain.economy import EconomyError
from packages.domain.economy_runtime import (
    economy_action_from_runtime_plan,
    runtime_economy_contributions,
)
from packages.runtime.src.lengeas_runtime.actions import ActionPlan, PlannedOperation
from packages.runtime.src.lengeas_runtime.conditions import Explanation


def test_trusted_runtime_resource_plan_becomes_conserved_economy_action() -> None:
    plan = ActionPlan(
        "quest_reward",
        "sha256:input",
        True,
        Explanation("condition", True, "passed"),
        (PlannedOperation("decrement", "core", "resource.coin.balance", 3, 0),),
        (),
        (
            PlannedOperation(
                "grant_resource",
                "core",
                None,
                {"type": "resource", "target": {"kind": "resource", "id": "gem"}, "quantity": 2},
                1,
            ),
        ),
        (),
        (),
        2,
    )
    action = economy_action_from_runtime_plan(plan)
    assert action.costs == {"coin": 3}
    assert action.grants == {"gem": 2}


def test_runtime_item_rewards_and_direct_resource_effects_are_rejected() -> None:
    denied = ActionPlan(
        "claim", "d", False, Explanation("condition", False, "denied"), (), (), (), (), (), 0
    )
    with pytest.raises(EconomyError, match="runtime_action_denied"):
        economy_action_from_runtime_plan(denied)
    item_reward = ActionPlan(
        "claim",
        "d",
        True,
        Explanation("condition", True, "passed"),
        (),
        (),
        (
            PlannedOperation(
                "grant_item",
                "core",
                None,
                {"type": "item", "target": {"kind": "item", "id": "item-1"}},
                0,
            ),
        ),
        (),
        (),
        1,
    )
    with pytest.raises(EconomyError, match="runtime_reward_requires_domain_handler"):
        economy_action_from_runtime_plan(item_reward)
    resource_action, item_intents = runtime_economy_contributions(item_reward)
    assert resource_action.costs == {}
    assert [(intent.item_id, intent.quantity) for intent in item_intents] == [("item-1", 1)]
