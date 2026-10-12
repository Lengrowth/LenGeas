from datetime import UTC, datetime

from packages.runtime.src.lengeas_runtime.actions import plan_action
from packages.runtime.src.lengeas_runtime.context import ExecutionContext
from packages.runtime.src.lengeas_runtime.registry import core_registry
from packages.runtime.src.lengeas_runtime.state_paths import StatePath, StatePathRegistry


def test_planner_orders_costs_effects_rewards_timers_and_events_without_mutation() -> None:
    registry = StatePathRegistry()
    token = "resource.gold.balance"
    registry.register(
        StatePath(token, "resource", "core", int, frozenset({"core"}), frozenset({"core"}))
    )
    registry.freeze()
    initial_state = {"resource": {"gold": {"balance": 10}}}
    context = ExecutionContext(
        "1.0.0",
        "sha256:definition",
        (("core", "sha256:package"),),
        4,
        "act_purchase",
        datetime(2030, 1, 1, tzinfo=UTC),
        123,
        (),
        "en",
        "actor",
        "studio",
        "game",
        "player",
        frozenset({"resource"}),
        frozenset({"resource"}),
    )
    action = {
        "id": "act_purchase",
        "input_schema": {"type": "object", "additionalProperties": False},
        "conditions": [
            {
                "expression": {
                    "operator": "gte",
                    "left": {"path": {"namespace_id": "resource", "segments": ["gold", "balance"]}},
                    "right": {"operator": "literal", "value": 3},
                }
            }
        ],
        "costs": [
            {
                "owner": "core",
                "target": {"kind": "resource", "id": "gold"},
                "quantity": {"expression": {"operator": "literal", "value": 3}, "variables": []},
                "insufficiency": "reject",
            }
        ],
        "effects": [
            {
                "operation": "increment",
                "path": {"namespace_id": "resource", "segments": ["gold", "balance"]},
                "value": 2,
            },
            {"operation": "start_timer", "target": {"kind": "timer", "id": "timer_tick"}},
            {
                "operation": "emit_event",
                "value": {"event_type": "resource.spent.v1", "payload": {"amount": 3}},
            },
        ],
        "rewards": [
            {
                "entries": [
                    {
                        "type": "resource",
                        "target": {"kind": "resource", "id": "gold"},
                        "quantity": 1,
                    }
                ]
            }
        ],
        "emitted_events": ["purchase.completed.v1"],
    }
    plan = plan_action(
        action,
        {},
        initial_state,
        context=context,
        path_registry=registry,
        handler_registry=core_registry(),
        timer_definitions={
            "timer_tick": {
                "authority": "server",
                "duration_formula": {
                    "expression": {"operator": "literal", "value": 500},
                    "variables": [],
                },
            }
        },
    )
    assert plan.allowed
    assert [op.kind for op in plan.costs + plan.effects + plan.rewards] == [
        "decrement",
        "increment",
        "start_timer",
        "emit_event",
        "grant_resource",
    ]
    assert plan.timers[0].due_at.isoformat() == "2030-01-01T00:00:00.500000+00:00"
    assert [event.event_type for event in plan.events] == [
        "resource.spent.v1",
        "purchase.completed.v1",
    ]
    assert initial_state == {"resource": {"gold": {"balance": 10}}}


def test_planner_denies_insufficient_cost_without_producing_effects() -> None:
    registry = StatePathRegistry()
    registry.register(
        StatePath(
            "resource.gold.balance",
            "resource",
            "core",
            int,
            frozenset({"core"}),
            frozenset({"core"}),
        )
    )
    registry.freeze()
    context = ExecutionContext(
        "1",
        "d",
        (),
        0,
        "act_cost",
        datetime(2030, 1, 1, tzinfo=UTC),
        0,
        (),
        "en",
        "a",
        "s",
        "g",
        "p",
        frozenset({"resource"}),
        frozenset({"resource"}),
    )
    plan = plan_action(
        {
            "id": "act_cost",
            "input_schema": {"type": "object"},
            "costs": [
                {
                    "target": {"kind": "resource", "id": "gold"},
                    "quantity": {"operator": "literal", "value": 3},
                }
            ],
            "effects": [{"operation": "increment", "path": "resource.gold.balance", "value": 1}],
        },
        {},
        {"resource": {"gold": {"balance": 1}}},
        context=context,
        path_registry=registry,
    )
    assert not plan.allowed
    assert plan.explanation.code == "insufficient_cost"
    assert not plan.effects
