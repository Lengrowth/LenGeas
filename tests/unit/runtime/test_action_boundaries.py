from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from packages.runtime.src.lengeas_runtime.actions import plan_action, validate_input
from packages.runtime.src.lengeas_runtime.context import ExecutionBudgets, ExecutionContext
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.registry import (
    HandlerOwner,
    HandlerRegistry,
    core_registry,
)
from packages.runtime.src.lengeas_runtime.state_paths import StatePath, StatePathRegistry


def make_context(**kwargs: Any) -> ExecutionContext:
    data: dict[str, Any] = {
        "engine_version": "1",
        "definition_digest": "sha256:def",
        "package_digests": (("core", "sha256:core"),),
        "state_version": 0,
        "action_id": "act",
        "logical_time": datetime(2030, 1, 1, tzinfo=UTC),
        "seed": 4,
        "experiment_assignments": (),
        "locale": "en",
        "actor_id": "a",
        "studio_id": "s",
        "game_id": "g",
        "player_id": "p",
        "readable_namespaces": frozenset({"player", "resource"}),
        "writable_namespaces": frozenset({"player", "resource"}),
    }
    data.update(kwargs)
    return ExecutionContext(**data)


def make_paths(
    *, value_type: type = int, writable: frozenset[str] = frozenset({"core"})
) -> StatePathRegistry:
    paths = StatePathRegistry()
    paths.register(
        StatePath(
            "resource.gold.balance",
            "resource",
            "core",
            value_type,
            frozenset({"core", "reader"}),
            writable,
        )
    )
    paths.freeze()
    return paths


def call(
    action: dict[str, Any],
    *,
    payload: Any = None,
    state: dict[str, Any] | None = None,
    context: ExecutionContext | None = None,
    paths: StatePathRegistry | None = None,
    handlers: HandlerRegistry | None = None,
) -> Any:
    return plan_action(
        action,
        {} if payload is None else payload,
        state or {"resource": {"gold": {"balance": 5}}},
        context=context or make_context(),
        path_registry=paths or make_paths(),
        handler_registry=handlers,
    )


@pytest.mark.parametrize(
    "payload,schema,code",
    [
        ([], {"type": "object"}, "action_input_type_invalid"),
        (
            {"n": True},
            {"type": "object", "properties": {"n": {"type": "integer"}}},
            "action_input_type_invalid",
        ),
        ({}, {"type": "object", "required": ["x"]}, "action_input_required"),
        ({"x": 1}, {"type": "object", "additionalProperties": False}, "action_input_unknown_field"),
        ({"x": 1}, {"type": "object", "properties": {"x": []}}, "action_input_schema_invalid"),
        (
            {"x": "a"},
            {"type": "object", "properties": {"x": {"type": "string", "pattern": "b+"}}},
            "action_input_pattern_invalid",
        ),
        (
            {"x": ""},
            {"type": "object", "properties": {"x": {"type": "string", "minLength": 1}}},
            "action_input_length_invalid",
        ),
        (
            {"x": 3},
            {"type": "object", "properties": {"x": {"type": "integer", "maximum": 2}}},
            "action_input_range_invalid",
        ),
        (
            {"x": 3},
            {"type": "object", "properties": {"x": {"const": 2}}},
            "action_input_const_invalid",
        ),
        (
            {"x": 3},
            {"type": "object", "properties": {"x": {"enum": [1, 2]}}},
            "action_input_enum_invalid",
        ),
        (
            {"x": [1]},
            {"type": "object", "properties": {"x": {"type": "array", "items": []}}},
            "action_input_schema_invalid",
        ),
    ],
)
def test_input_validation_rejects_invalid_shapes(
    payload: Any, schema: dict[str, Any], code: str
) -> None:
    with pytest.raises(RuntimeErrorCode, match=code):
        validate_input(payload, schema)


def test_input_schema_success_paths_and_properties_shape() -> None:
    with pytest.raises(RuntimeErrorCode, match="action_input_schema_invalid"):
        validate_input({}, {"type": "object", "properties": []})
    validate_input(
        {"tags": ["a", "b"], "code": "abc", "value": 3},
        {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
                "code": {"type": "string", "pattern": "[a-z]+", "minLength": 2},
                "value": {"type": "integer", "minimum": 0, "maximum": 5},
            },
        },
    )
    validate_input([], {"type": "array", "items": {"type": "integer"}})


def test_input_validation_limits_nested_values_and_depth() -> None:
    with pytest.raises(RuntimeErrorCode, match="action_input_limit_exceeded"):
        validate_input("x" * 5000, {"type": "string"})
    with pytest.raises(RuntimeErrorCode, match="action_input_limit_exceeded"):
        validate_input([0, 1], {"type": "array", "maxItems": 1})
    schema: dict[str, Any] = {"type": "integer"}
    value: Any = 1
    for _ in range(34):
        schema = {"type": "array", "items": schema}
        value = [value]
    with pytest.raises(RuntimeErrorCode, match="action_input_depth_exceeded"):
        validate_input(value, schema)
    with pytest.raises(RuntimeErrorCode, match="action_input_schema_invalid"):
        validate_input([1], {"type": "array", "items": "bad"})
    with pytest.raises(RuntimeErrorCode, match="action_input_limit_exceeded"):
        validate_input({str(i): i for i in range(257)}, {"type": "object"})
    with pytest.raises(RuntimeErrorCode, match="action_input_limit_exceeded"):
        validate_input(list(range(257)), {"type": "array"})
    with pytest.raises(RuntimeErrorCode, match="action_input_limit_exceeded"):
        validate_input("x" * 20, {"type": "string", "maxLength": 2})


def test_planner_registry_condition_cost_and_namespace_guards() -> None:
    mutable = HandlerRegistry()
    with pytest.raises(RuntimeErrorCode, match="registry_must_be_frozen"):
        call({}, handlers=mutable)
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        call({"conditions": "bad"})
    denied = call(
        {
            "conditions": [{"operator": "eq", "left": 1, "right": 2}],
            "effects": [{"operation": "increment", "path": "resource.gold.balance", "value": 1}],
        }
    )
    assert denied.allowed is False and not denied.effects
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        call({"costs": [{"target": None, "quantity": 1}]})
    with pytest.raises(RuntimeErrorCode, match="state_path_unregistered"):
        call({"costs": [{"target": "resource.gold.unknown", "quantity": 1}]})
    with pytest.raises(RuntimeErrorCode, match="namespace_owner_mismatch"):
        call(
            {"costs": [{"owner": "reader", "target": "resource.gold.balance", "quantity": 1}]},
            paths=make_paths(writable=frozenset({"core", "reader"})),
        )
    read_only = make_paths(writable=frozenset({"core"}))
    context = make_context(writable_namespaces=frozenset())
    with pytest.raises(RuntimeErrorCode, match="namespace_access_denied"):
        call(
            {"costs": [{"target": "resource.gold.balance", "quantity": 1}]},
            context=context,
            paths=read_only,
        )


def test_planner_partial_cost_formula_and_scale_loss() -> None:
    plan = call(
        {"costs": [{"target": "resource.gold.balance", "quantity": 8, "insufficiency": "partial"}]}
    )
    assert plan.allowed and plan.costs[0].value == 5
    with pytest.raises(RuntimeErrorCode, match="numeric_scale_loss"):
        call({"costs": [{"target": "resource.gold.balance", "quantity": "1.5"}]})
    call(
        {
            "costs": [
                {
                    "target": {"namespace_id": "resource", "segments": ["gold", "balance"]},
                    "quantity": 1,
                }
            ]
        }
    )


def test_effect_expansion_package_timer_event_and_budget_guards() -> None:
    handlers = HandlerRegistry()
    handlers.register_effect(
        "custom", HandlerOwner("other", "resource", "sha256:x"), lambda _state, raw: (raw,)
    )
    handlers.freeze()
    with pytest.raises(RuntimeErrorCode, match="handler_package_mismatch"):
        call({"effects": [{"operation": "custom"}]}, handlers=handlers)
    with pytest.raises(RuntimeErrorCode, match="effect_handler_missing"):
        call({"effects": [{"operation": "unknown"}]})
    reader_handlers = HandlerRegistry()
    reader_handlers.register_effect(
        "custom", HandlerOwner("reader", "resource", "sha256:x"), lambda _state, raw: (raw,)
    )
    reader_handlers.freeze()
    read_only_path = make_paths(writable=frozenset({"core"}))
    with pytest.raises(RuntimeErrorCode, match="state_path_write_denied"):
        call(
            {
                "effects": [
                    {
                        "operation": "custom",
                        "owner": "reader",
                        "path": "resource.gold.balance",
                        "value": 1,
                    }
                ]
            },
            handlers=reader_handlers,
            paths=read_only_path,
        )
    with pytest.raises(RuntimeErrorCode, match="timer_plan_invalid"):
        call({"effects": [{"operation": "start_timer", "timer_id": "t", "duration_ms": -1}]})
    with pytest.raises(RuntimeErrorCode, match="effect_budget_exceeded"):
        call(
            {"effects": [{"operation": "increment", "path": "resource.gold.balance", "value": 1}]},
            context=make_context(budgets=ExecutionBudgets(effects=0)),
        )
    with pytest.raises(RuntimeErrorCode, match="event_budget_exceeded"):
        call({"emitted_events": ["one"]}, context=make_context(budgets=ExecutionBudgets(events=0)))
    with pytest.raises(RuntimeErrorCode, match="state_patch_budget_exceeded"):
        call(
            {"effects": [{"operation": "set", "path": "resource.gold.balance", "value": "x" * 50}]},
            context=make_context(budgets=ExecutionBudgets(state_patch_bytes=1)),
        )


def test_effect_namespace_formula_timer_and_event_fallbacks() -> None:
    context = make_context(writable_namespaces=frozenset())
    with pytest.raises(RuntimeErrorCode, match="namespace_access_denied"):
        call(
            {"effects": [{"operation": "increment", "path": "resource.gold.balance", "value": 1}]},
            context=context,
        )
    plan = call(
        {
            "effects": [
                {
                    "operation": "set",
                    "target": {"kind": "resource", "id": "gold"},
                    "value": {
                        "operator": "add",
                        "args": [
                            {"operator": "literal", "value": 1},
                            {"operator": "literal", "value": 2},
                        ],
                    },
                },
                {"operation": "start_timer", "timer_id": "t", "duration_ms": 0},
                {"operation": "emit_event", "value": "not-an-object"},
            ]
        }
    )
    assert plan.effects[0].path == "resource.gold.balance"
    assert plan.effects[0].value == 3
    assert plan.timers[0].due_at == make_context().logical_time
    assert plan.events[0].event_type == "runtime.changed.v1"
    text_paths = make_paths(value_type=str)
    text_plan = call(
        {
            "effects": [
                {
                    "operation": "set",
                    "path": "resource.gold.balance",
                    "value": {"operator": "literal", "value": "12"},
                }
            ]
        },
        paths=text_paths,
    )
    assert text_plan.effects[0].value == "12"
    decimal_paths = make_paths(value_type=Decimal)
    decimal_plan = call(
        {
            "effects": [
                {
                    "operation": "set",
                    "path": "resource.gold.balance",
                    "value": {"operator": "literal", "value": "1.25"},
                }
            ]
        },
        paths=decimal_paths,
    )
    assert decimal_plan.effects[0].value == Decimal("1.25")
    timer_plan = call(
        {"effects": [{"operation": "start_timer", "timer_id": "t", "duration_ms": 10}]},
        context=make_context(),
    )
    assert timer_plan.timers[0].due_at.microsecond == 10_000


def test_reward_and_event_definitions_are_validated() -> None:
    with pytest.raises(RuntimeErrorCode, match="reward_entries_invalid"):
        call({"rewards": [{"entries": "bad"}]})
    with pytest.raises(RuntimeErrorCode, match="reward_entries_invalid"):
        call({"rewards": [{"entries": [None]}]})
    with pytest.raises(RuntimeErrorCode, match="reward_handler_missing"):
        call({"rewards": [{"entries": [{"type": "unknown"}]}]})
    with pytest.raises(RuntimeErrorCode, match="event_definition_invalid"):
        call({"emitted_events": "not a list"})


def test_core_registry_is_frozen_and_cost_denial_is_explained() -> None:
    registry = core_registry()
    assert registry.frozen
    result = call({"costs": [{"target": "resource.gold.balance", "quantity": Decimal("10")}]})
    assert result.allowed is False
