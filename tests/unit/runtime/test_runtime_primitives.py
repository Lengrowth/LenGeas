from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from packages.runtime.src.lengeas_runtime.conditions import evaluate_condition
from packages.runtime.src.lengeas_runtime.context import ExecutionBudgets, ExecutionContext
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula
from packages.runtime.src.lengeas_runtime.registry import (
    HandlerOwner,
    HandlerRegistry,
    core_registry,
)
from packages.runtime.src.lengeas_runtime.state_paths import (
    MissingRule,
    StatePath,
    StatePathRegistry,
)


def make_context() -> ExecutionContext:
    return ExecutionContext(
        "1.0.0",
        "sha256:def",
        (("core", "sha256:pkg"),),
        3,
        "act_test",
        datetime(2030, 1, 1, tzinfo=UTC),
        9,
        (),
        "en",
        "actor",
        "studio",
        "game",
        "player",
        frozenset({"player"}),
        frozenset({"player"}),
        ExecutionBudgets(),
    )


def test_context_is_immutable_and_canonicalizes_pinned_inputs() -> None:
    context = make_context()
    assert context.logical_time.tzinfo == UTC
    assert context.package_digests == (("core", "sha256:pkg"),)
    assert context.execution_tuple[-1] == 9
    with pytest.raises((AttributeError, TypeError)):
        context.seed = 10  # type: ignore[misc]


def test_context_rejects_naive_time_and_invalid_seed() -> None:
    with pytest.raises(RuntimeErrorCode, match="logical_time_must_be_aware"):
        ExecutionContext(
            "1",
            "d",
            (),
            0,
            "a",
            datetime(2030, 1, 1),
            0,
            (),
            "en",
            "a",
            "s",
            "g",
            "p",
            frozenset(),
            frozenset(),
        )
    with pytest.raises(RuntimeErrorCode, match="execution_context_invalid"):
        ExecutionContext(
            "1",
            "d",
            (),
            0,
            "a",
            datetime(2030, 1, 1, tzinfo=UTC),
            2**128,
            (),
            "en",
            "a",
            "s",
            "g",
            "p",
            frozenset(),
            frozenset(),
        )


def test_state_path_checks_read_write_owner_and_missing_rule() -> None:
    registry = StatePathRegistry()
    registry.register(
        StatePath(
            "player.level", "player", "core", int, frozenset({"core", "story"}), frozenset({"core"})
        )
    )
    registry.register(
        StatePath(
            "player.optional",
            "player",
            "core",
            str,
            frozenset({"core"}),
            frozenset({"core"}),
            MissingRule.ALLOW_ABSENCE,
        )
    )
    registry.freeze()
    assert registry.read({"player": {"level": 5}}, "player.level", "story") == 5
    with pytest.raises(RuntimeErrorCode, match="state_path_write_denied"):
        registry.resolve("player.level", "story", write=True)
    with pytest.raises(RuntimeErrorCode, match="state_path_unregistered"):
        registry.resolve("player.arbitrary", "core")


def test_condition_explanations_and_boolean_order() -> None:
    registry = StatePathRegistry()
    registry.register(
        StatePath("player.level", "player", "core", int, frozenset({"core"}), frozenset({"core"}))
    )
    registry.freeze()
    result = evaluate_condition(
        {
            "operator": "all",
            "conditions": [
                {
                    "operator": "gte",
                    "left": {"operator": "state", "path": "player.level"},
                    "right": {"operator": "literal", "value": 4},
                },
                {
                    "operator": "lt",
                    "left": {"operator": "state", "path": "player.level"},
                    "right": {"operator": "literal", "value": 9},
                },
            ],
        },
        {"player": {"level": 5}},
        registry,
        "core",
        datetime(2030, 1, 1, tzinfo=UTC),
    )
    assert result.passed and len(result.children) == 2
    assert result.as_dict()["code"] == "condition_met"


def test_formula_decimal_operations_and_limits() -> None:
    ast = {
        "operator": "divide",
        "args": [
            {
                "operator": "multiply",
                "args": [
                    {"operator": "literal", "value": "1.5"},
                    {"operator": "literal", "value": 3},
                ],
            },
            {"operator": "literal", "value": 2},
        ],
    }
    assert evaluate_formula(ast, {}) == Decimal("2.25")
    with pytest.raises(RuntimeErrorCode, match="division_by_zero"):
        evaluate_formula(
            {
                "operator": "divide",
                "args": [{"operator": "literal", "value": 2}, {"operator": "literal", "value": 0}],
            },
            {},
        )
    with pytest.raises(RuntimeErrorCode, match="formula_variable_not_allowed"):
        evaluate_formula(
            {"operator": "variable", "name": "x"}, {"x": 1}, allowed_variables=frozenset()
        )
    with pytest.raises(RuntimeErrorCode, match="formula_operation_budget_exceeded"):
        evaluate_formula(
            {
                "operator": "add",
                "args": [{"operator": "literal", "value": 1}, {"operator": "literal", "value": 2}],
            },
            {},
            max_operations=2,
        )
    with pytest.raises(RuntimeErrorCode, match="numeric_overflow"):
        evaluate_formula(
            {
                "operator": "add",
                "args": [
                    {"operator": "literal", "value": 2**63 - 1},
                    {"operator": "literal", "value": 1},
                ],
            },
            {},
        )
    with pytest.raises(RuntimeErrorCode, match="numeric_scale_exceeded"):
        evaluate_formula(
            {
                "operator": "divide",
                "args": [
                    {"operator": "literal", "value": 1},
                    {"operator": "literal", "value": 3},
                ],
            },
            {},
        )


def test_formula_piecewise_and_numeric_operators() -> None:
    piecewise = {
        "operator": "piecewise",
        "cases": [
            {
                "when": {"operator": "eq", "left": 2, "right": 2},
                "then": {
                    "operator": "power_integer",
                    "args": [
                        {"operator": "literal", "value": 2},
                        {"operator": "literal", "value": 3},
                    ],
                },
            }
        ],
        "fallback": {"operator": "literal", "value": 0},
    }
    assert evaluate_formula(piecewise, {}, condition=lambda ast: ast["left"] == ast["right"]) == 8
    assert (
        evaluate_formula(
            {
                "operator": "subtract",
                "args": [
                    {"operator": "literal", "value": 10},
                    {"operator": "literal", "value": 2},
                    {"operator": "literal", "value": 1},
                ],
            },
            {},
        )
        == 7
    )
    assert (
        evaluate_formula(
            {"operator": "floor", "args": [{"operator": "literal", "value": "2.9"}]}, {}
        )
        == 2
    )
    assert (
        evaluate_formula(
            {"operator": "ceil", "args": [{"operator": "literal", "value": "2.1"}]}, {}
        )
        == 3
    )
    assert (
        evaluate_formula(
            {
                "operator": "min",
                "args": [{"operator": "literal", "value": 3}, {"operator": "literal", "value": 1}],
            },
            {},
        )
        == 1
    )
    assert (
        evaluate_formula(
            {
                "operator": "max",
                "args": [{"operator": "literal", "value": 3}, {"operator": "literal", "value": 1}],
            },
            {},
        )
        == 3
    )


def test_temporal_membership_existence_and_registered_predicate_conditions() -> None:
    registry = StatePathRegistry()
    registry.register(
        StatePath(
            "player.started",
            "player",
            "core",
            datetime,
            frozenset({"core"}),
            frozenset({"core"}),
            MissingRule.ALLOW_ABSENCE,
        )
    )
    registry.freeze()
    now = datetime(2030, 1, 1, tzinfo=UTC)
    assert evaluate_condition(
        {"operator": "before", "at": "2031-01-01T00:00:00Z"}, {}, registry, "core", now
    ).passed
    assert evaluate_condition(
        {"operator": "elapsed_at_least", "path": "player.started", "duration_seconds": 10},
        {"player": {"started": datetime(2029, 12, 31, 23, 59, 40, tzinfo=UTC)}},
        registry,
        "core",
        now,
    ).passed
    assert not evaluate_condition(
        {"operator": "exists", "path": "player.started"}, {"player": {}}, registry, "core", now
    ).passed
    assert evaluate_condition(
        {"operator": "in", "value": 2, "values": [1, 2, 3]}, {}, registry, "core", now
    ).passed
    assert evaluate_condition(
        {"operator": "predicate", "name": "is_ready", "arguments": {}},
        {},
        registry,
        "core",
        now,
        predicates={"is_ready": lambda _args: True},
    ).passed


def test_registries_are_frozen_and_enforce_package_owner() -> None:
    registry = HandlerRegistry()
    owner = HandlerOwner("core", "core", "sha256:p")
    registry.register_effect("set", owner, lambda _state, value: (value,))
    assert registry.effect("set", "core", {}, {"path": "core.x"})[0]["path"] == "core.x"
    with pytest.raises(RuntimeErrorCode, match="handler_package_mismatch"):
        registry.effect("set", "other", {}, {})
    registry.freeze()
    with pytest.raises(RuntimeErrorCode, match="registry_frozen"):
        registry.register_effect("new", owner, lambda _state, value: (value,))
    assert core_registry().frozen
