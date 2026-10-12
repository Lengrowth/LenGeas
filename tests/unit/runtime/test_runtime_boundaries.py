from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from packages.runtime.src.lengeas_runtime.conditions import evaluate_condition
from packages.runtime.src.lengeas_runtime.context import ExecutionBudgets, ExecutionContext
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula
from packages.runtime.src.lengeas_runtime.registry import HandlerOwner, HandlerRegistry
from packages.runtime.src.lengeas_runtime.rng import PCG64
from packages.runtime.src.lengeas_runtime.serialization import (
    canonical_bytes,
    digest,
    freeze_value,
    thaw_value,
)
from packages.runtime.src.lengeas_runtime.state_paths import (
    MissingRule,
    StatePath,
    StatePathRegistry,
    path_token,
)


def path_registry(
    value_type: type = int, missing: MissingRule = MissingRule.ERROR
) -> StatePathRegistry:
    registry = StatePathRegistry()
    registry.register(
        StatePath(
            "player.value",
            "player",
            "core",
            value_type,
            frozenset({"core", "reader"}),
            frozenset({"core"}),
            missing,
        )
    )
    registry.freeze()
    return registry


def context(**changes: object) -> ExecutionContext:
    values: dict[str, object] = {
        "engine_version": "1.0.0",
        "definition_digest": "sha256:def",
        "package_digests": (("core", "sha256:core"),),
        "state_version": 0,
        "action_id": "act_test",
        "logical_time": datetime(2030, 1, 1, tzinfo=UTC),
        "seed": 1,
        "experiment_assignments": (),
        "locale": "en",
        "actor_id": "actor",
        "studio_id": "studio",
        "game_id": "game",
        "player_id": "player",
        "readable_namespaces": frozenset({"player"}),
        "writable_namespaces": frozenset({"player"}),
    }
    values.update(changes)
    return ExecutionContext(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "operator,left,right,expected",
    [
        ("eq", 2, 2, True),
        ("ne", 2, 3, True),
        ("lt", 2, 3, True),
        ("lte", 2, 2, True),
        ("gt", 3, 2, True),
        ("gte", 2, 2, True),
    ],
)
def test_all_condition_comparisons(operator: str, left: int, right: int, expected: bool) -> None:
    result = evaluate_condition(
        {"operator": operator, "left": left, "right": right},
        {},
        path_registry(),
        "core",
        datetime(2030, 1, 1, tzinfo=UTC),
    )
    assert result.passed is expected


def test_condition_absence_type_budget_ast_and_predicate_errors() -> None:
    now = datetime(2030, 1, 1, tzinfo=UTC)
    registry = path_registry(missing=MissingRule.ALLOW_ABSENCE)
    assert evaluate_condition(
        {"operator": "exists", "path": "player.value"},
        {"player": {"value": 1}},
        registry,
        "core",
        now,
    ).passed
    with pytest.raises(RuntimeErrorCode, match="condition_type_mismatch"):
        evaluate_condition({"operator": "lt", "left": 1, "right": "1"}, {}, registry, "core", now)
    with pytest.raises(RuntimeErrorCode, match="condition_budget_exceeded"):
        evaluate_condition(
            {"operator": "all", "args": [{"operator": "eq", "left": 1, "right": 1}]},
            {},
            registry,
            "core",
            now,
            max_nodes=1,
        )
    with pytest.raises(RuntimeErrorCode, match="condition_operator_unknown"):
        evaluate_condition({"operator": "wat"}, {}, registry, "core", now)
    with pytest.raises(RuntimeErrorCode, match="condition_predicate_unregistered"):
        evaluate_condition(
            {"operator": "predicate", "name": "missing", "arguments": {}}, {}, registry, "core", now
        )
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        evaluate_condition(
            {"operator": "predicate", "name": "p", "arguments": []},
            {},
            registry,
            "core",
            now,
            predicates={"p": lambda _args: True},
        )
    with pytest.raises(RuntimeErrorCode, match="condition_operand_invalid"):
        evaluate_condition(
            {"operator": "eq", "left": {"operator": "unknown"}, "right": 1},
            {},
            registry,
            "core",
            now,
        )
    with pytest.raises(RuntimeErrorCode, match="condition_timestamp_invalid"):
        evaluate_condition({"operator": "before", "at": "not-a-time"}, {}, registry, "core", now)


def test_temporal_after_and_elapsed_timestamp_validation() -> None:
    now = datetime(2030, 1, 1, tzinfo=UTC)
    assert evaluate_condition(
        {"operator": "after", "at": "2029-01-01T00:00:00Z"}, {}, path_registry(), "core", now
    ).passed
    with pytest.raises(RuntimeErrorCode, match="condition_timestamp_invalid"):
        evaluate_condition(
            {"operator": "elapsed_at_least", "path": "player.value", "duration_seconds": 1},
            {"player": {"value": 1}},
            path_registry(),
            "core",
            now,
        )


@pytest.mark.parametrize(
    "expression,expected",
    [
        (
            {
                "operator": "add",
                "args": [
                    {"operator": "literal", "value": 1},
                    {"operator": "literal", "value": 2},
                    {"operator": "literal", "value": 3},
                ],
            },
            6,
        ),
        (
            {
                "operator": "multiply",
                "args": [
                    {"operator": "literal", "value": 2},
                    {"operator": "literal", "value": 3},
                    {"operator": "literal", "value": 4},
                ],
            },
            24,
        ),
        (
            {
                "operator": "divide",
                "args": [
                    {"operator": "literal", "value": 12},
                    {"operator": "literal", "value": 2},
                    {"operator": "literal", "value": 3},
                ],
            },
            2,
        ),
        (
            {
                "operator": "clamp",
                "args": [
                    {"operator": "literal", "value": 12},
                    {"operator": "literal", "value": 0},
                    {"operator": "literal", "value": 10},
                ],
            },
            10,
        ),
        (
            {
                "operator": "power_integer",
                "args": [{"operator": "literal", "value": 2}, {"operator": "literal", "value": -2}],
            },
            Decimal("0.25"),
        ),
    ],
)
def test_numeric_operator_boundaries(
    expression: dict[str, object], expected: int | Decimal
) -> None:
    assert evaluate_formula(expression, {}) == expected


def test_formula_invalid_shapes_scales_variables_and_piecewise_fallback() -> None:
    with pytest.raises(RuntimeErrorCode, match="formula_ast_invalid"):
        evaluate_formula([], {})  # type: ignore[arg-type]
    with pytest.raises(RuntimeErrorCode, match="formula_operator_unknown"):
        evaluate_formula({"operator": "wat"}, {})
    with pytest.raises(RuntimeErrorCode, match="formula_variable_missing"):
        evaluate_formula({"operator": "variable", "name": "missing"}, {})
    with pytest.raises(RuntimeErrorCode, match="formula_number_invalid"):
        evaluate_formula({"operator": "literal", "value": True}, {})
    with pytest.raises(RuntimeErrorCode, match="formula_exponent_invalid"):
        evaluate_formula(
            {
                "operator": "power_integer",
                "args": [
                    {"operator": "literal", "value": 2},
                    {"operator": "literal", "value": "1.5"},
                ],
            },
            {},
        )
    with pytest.raises(RuntimeErrorCode, match="formula_piecewise_condition_context_required"):
        evaluate_formula(
            {"operator": "piecewise", "cases": [], "fallback": {"operator": "literal", "value": 1}},
            {},
        )
    result = evaluate_formula(
        {
            "operator": "piecewise",
            "cases": [
                {
                    "when": {"operator": "eq", "left": 1, "right": 2},
                    "then": {"operator": "literal", "value": 1},
                }
            ],
            "fallback": {"operator": "literal", "value": 7},
        },
        {},
        condition=lambda _ast: False,
    )
    assert result == 7


def test_formula_wrapper_enforces_declared_variable_allowlist() -> None:
    with pytest.raises(RuntimeErrorCode, match="formula_variable_not_allowed"):
        evaluate_formula(
            {"expression": {"operator": "variable", "name": "y"}, "variables": ["x"]},
            {"x": 1, "y": 2},
        )


def test_path_registry_failures_and_schema_tokens() -> None:
    registry = StatePathRegistry()
    valid = StatePath(
        "player.value", "player", "core", int, frozenset({"core"}), frozenset({"core"})
    )
    registry.register(valid)
    with pytest.raises(RuntimeErrorCode, match="state_path_duplicate"):
        registry.register(valid)
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        registry.register(
            StatePath("player.Bad", "player", "core", int, frozenset({"core"}), frozenset({"core"}))
        )
    registry.freeze()
    with pytest.raises(RuntimeErrorCode, match="registry_frozen"):
        registry.register(
            StatePath(
                "player.other", "player", "core", int, frozenset({"core"}), frozenset({"core"})
            )
        )
    with pytest.raises(RuntimeErrorCode, match="state_path_read_denied"):
        registry.read({"player": {"value": 1}}, "player.value", "writer")
    with pytest.raises(RuntimeErrorCode, match="state_path_missing"):
        registry.read({"player": {}}, "player.value", "core")
    with pytest.raises(RuntimeErrorCode, match="state_path_type_mismatch"):
        registry.read({"player": {"value": True}}, "player.value", "core")
    assert path_token({"namespace_id": "player", "segments": ["value"]}) == "player.value"
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        path_token({"namespace_id": "player", "segments": []})


def test_registry_missing_handler_duplicate_and_bad_reward_errors() -> None:
    registry = HandlerRegistry()
    owner = HandlerOwner("core", "player", "sha256:package")

    def handler(_state: object, value: object) -> tuple[object, ...]:
        return (value,)

    registry.register_effect("set", owner, handler)
    registry.register_reward("resource", owner, lambda payload: (payload,))
    with pytest.raises(RuntimeErrorCode, match="effect_handler_duplicate"):
        registry.register_effect("set", owner, handler)
    with pytest.raises(RuntimeErrorCode, match="reward_handler_duplicate"):
        registry.register_reward("resource", owner, lambda payload: (payload,))
    registry.freeze()
    with pytest.raises(RuntimeErrorCode, match="effect_handler_missing"):
        registry.effect("increment", "core", {}, {})
    with pytest.raises(RuntimeErrorCode, match="reward_handler_missing"):
        registry.reward("item", "core", {})


@pytest.mark.parametrize("value", [date(2030, 1, 1), float("nan"), float("inf"), object()])
def test_canonical_serializer_rejects_unsupported_values(value: object) -> None:
    with pytest.raises(RuntimeErrorCode):
        canonical_bytes({"value": value})


def test_canonical_serializer_normalizes_utc_and_freezes_nested_values() -> None:
    frozen = freeze_value({"a": [1, {"b": 2}]})
    assert thaw_value(frozen) == {"a": [1, {"b": 2}]}
    assert canonical_bytes({"when": datetime(2030, 1, 1, tzinfo=UTC)}) == (
        b'{"when":"2030-01-01T00:00:00.000000Z"}'
    )
    assert digest({"b": 1, "a": 2}) == digest({"a": 2, "b": 1})
    with pytest.raises(RuntimeErrorCode, match="timestamp_must_be_aware"):
        canonical_bytes(datetime(2030, 1, 1))


def test_context_budget_and_seed_failures_and_rng_bounds() -> None:
    with pytest.raises(RuntimeErrorCode, match="budget_invalid"):
        ExecutionBudgets(effects=-1)
    with pytest.raises(RuntimeErrorCode, match="execution_inputs_unpinned"):
        context(engine_version="")
    with pytest.raises(RuntimeErrorCode, match="seed_invalid"):
        PCG64.from_seed(2**128)
    generator = PCG64.from_seed(7)
    with pytest.raises(RuntimeErrorCode, match="random_bound_invalid"):
        generator.randbelow(0)
    assert 0 <= PCG64.from_seed(1).randbelow(2**64) < 2**64


def test_condition_remaining_paths_and_explanations() -> None:
    now = datetime(2030, 1, 1, tzinfo=UTC)
    registry = StatePathRegistry()
    registry.register(
        StatePath(
            "player.value",
            "player",
            "core",
            datetime,
            frozenset({"core", "reader"}),
            frozenset({"core"}),
            MissingRule.ALLOW_ABSENCE,
        )
    )
    registry.freeze()
    state = {"player": {"value": datetime(2029, 12, 31, tzinfo=UTC)}}
    assert evaluate_condition(
        {
            "expression": {
                "operator": "not",
                "args": [{"operator": "before", "at": "2029-01-01T00:00:00Z"}],
            }
        },
        state,
        registry,
        "core",
        now,
    ).passed
    assert not evaluate_condition(
        {"operator": "exists", "path": "player.value"},
        {},
        registry,
        "core",
        now,
    ).passed
    with pytest.raises(RuntimeErrorCode, match="condition_duration_invalid"):
        evaluate_condition(
            {"operator": "elapsed_at_least", "path": "player.value", "duration_seconds": True},
            state,
            registry,
            "core",
            now,
        )
    with pytest.raises(RuntimeErrorCode, match="condition_timestamp_invalid"):
        evaluate_condition(
            {"operator": "before", "at": "2030-01-01T00:00:00"},
            state,
            registry,
            "core",
            now,
        )
    with pytest.raises(RuntimeErrorCode, match="condition_operand_missing"):
        evaluate_condition(
            {"operator": "eq", "left": {"path": "player.value"}, "right": 1},
            {},
            registry,
            "core",
            now,
        )
    assert evaluate_condition(
        {"operator": "in", "value": 2, "values": [1, 2]}, {}, registry, "core", now
    ).passed
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        evaluate_condition(
            {"operator": "in", "value": 2, "values": "bad"}, {}, registry, "core", now
        )
    assert evaluate_condition(
        {"operator": "predicate", "name": "yes", "arguments": {}},
        {},
        registry,
        "core",
        now,
        predicates={"yes": lambda _args: True},
    ).passed
    with pytest.raises(RuntimeErrorCode, match="condition_budget_exceeded"):
        evaluate_condition(
            {"operator": "eq", "left": 1, "right": 1}, {}, registry, "core", now, max_depth=0
        )
    logical_time_condition = evaluate_condition(
        {"operator": "eq", "left": {"operator": "logical_time"}, "right": now},
        state,
        registry,
        "core",
        now,
    )
    assert logical_time_condition.passed
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        evaluate_condition({"operator": "all", "conditions": None}, state, registry, "core", now)
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        evaluate_condition({"operator": "all", "args": [None]}, state, registry, "core", now)
    with pytest.raises(RuntimeErrorCode, match="condition_ast_invalid"):
        evaluate_condition({"operator": "not", "args": []}, state, registry, "core", now)
    required = StatePathRegistry()
    required.register(
        StatePath("player.value", "player", "core", int, frozenset({"core"}), frozenset({"core"}))
    )
    absent = evaluate_condition(
        {"operator": "exists", "path": "player.value"}, {}, required, "core", now
    )
    assert not absent.passed and absent.code == "state_absent"


def test_formula_remaining_errors_and_operators() -> None:
    for operator, args, code in [
        ("clamp", [3, 5, 1], "formula_range_invalid"),
        ("divide", [1, 0], "division_by_zero"),
        ("piecewise", [], "formula_piecewise_no_match"),
    ]:
        ast: dict[str, object] = {
            "operator": operator,
            "args": [{"operator": "literal", "value": value} for value in args],
        }
        if operator == "piecewise":
            ast.update({"cases": [], "fallback": None})
        if operator == "piecewise":
            with pytest.raises(RuntimeErrorCode, match=code):
                evaluate_formula(ast, {}, condition=lambda _condition: False)
        else:
            with pytest.raises(RuntimeErrorCode, match=code):
                evaluate_formula(ast, {})
    assert (
        evaluate_formula(
            {"operator": "floor", "args": [{"operator": "literal", "value": "1.9"}]}, {}
        )
        == 1
    )
    assert (
        evaluate_formula(
            {"operator": "ceil", "args": [{"operator": "literal", "value": "1.1"}]}, {}
        )
        == 2
    )
    with pytest.raises(RuntimeErrorCode, match="formula_ast_invalid"):
        evaluate_formula({"operator": "add", "args": "invalid"}, {})
    with pytest.raises(RuntimeErrorCode, match="formula_operation_budget_exceeded"):
        evaluate_formula(
            {"operator": "add", "args": [{"operator": "literal", "value": 1}]}, {}, max_operations=1
        )
    with pytest.raises(RuntimeErrorCode, match="numeric_overflow"):
        evaluate_formula({"operator": "literal", "value": "999999999999999999999"}, {})
    with pytest.raises(RuntimeErrorCode, match="numeric_scale_exceeded"):
        evaluate_formula({"operator": "literal", "value": "0.0000000001"}, {})
    with pytest.raises(RuntimeErrorCode, match="formula_number_invalid"):
        evaluate_formula({"operator": "literal", "value": "nope"}, {})
    assert (
        evaluate_formula(
            {"operator": "variable", "name": "x"}, {"x": 5}, allowed_variables=frozenset({"x"})
        )
        == 5
    )
    with pytest.raises(RuntimeErrorCode, match="formula_variable_not_allowed"):
        evaluate_formula(
            {"expression": {"operator": "variable", "name": "x"}, "variables": ["y"]},
            {"x": 1},
            allowed_variables=frozenset({"y"}),
        )
    with pytest.raises(RuntimeErrorCode, match="formula_ast_invalid"):
        evaluate_formula(
            {
                "operator": "piecewise",
                "cases": "bad",
                "fallback": {"operator": "literal", "value": 1},
            },
            {},
            condition=lambda _condition: True,
        )
    with pytest.raises(RuntimeErrorCode, match="numeric_overflow"):
        evaluate_formula(
            {
                "operator": "power_integer",
                "args": [
                    {"operator": "literal", "value": "999999"},
                    {"operator": "literal", "value": 16},
                ],
            },
            {},
        )


def test_registry_path_serializer_and_error_edges() -> None:
    from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode

    error = RuntimeErrorCode("stable_code", "readable message")
    assert error.as_dict() == {"code": "stable_code", "message": "readable message"}
    with pytest.raises(RuntimeErrorCode, match="registry_frozen"):
        HandlerRegistry().freeze()
        frozen = HandlerRegistry()
        frozen.freeze()
        frozen.register_effect("x", HandlerOwner("core", "player", "d"), lambda _s, _p: ())
    with pytest.raises(RuntimeErrorCode, match="handler_package_mismatch"):
        handlers = HandlerRegistry()
        handlers.register_effect("x", HandlerOwner("core", "player", "d"), lambda _s, _p: ())
        handlers.effect("x", "other", {}, {})
    with pytest.raises(RuntimeErrorCode, match="reward_entries_invalid"):
        from packages.runtime.src.lengeas_runtime.registry import core_registry

        core_registry().reward("resource", "core", {"entries": "bad"})
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        StatePathRegistry().register(
            StatePath("player.Bad", "wrong", "core", int, frozenset({"core"}), frozenset({"core"}))
        )
    paths = StatePathRegistry()
    paths.register(
        StatePath(
            "player.value",
            "player",
            "core",
            int,
            frozenset({"core"}),
            frozenset({"core"}),
            MissingRule.ALLOW_ABSENCE,
        )
    )
    paths.freeze()
    with pytest.raises(RuntimeErrorCode, match="state_path_write_denied"):
        paths.resolve("player.value", "reader", write=True)
    missing_registry = StatePathRegistry()
    missing_registry.register(
        StatePath("player.value", "player", "core", int, frozenset({"core"}), frozenset({"core"}))
    )
    with pytest.raises(RuntimeErrorCode, match="state_path_missing"):
        missing_registry.read({}, "player.value", "core")
    assert paths.read({}, "player.value", "core") is not None
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        path_token({"namespace_id": 3, "segments": ["x"]})
    with pytest.raises(RuntimeErrorCode, match="state_path_invalid"):
        path_token({"namespace_id": "player", "segments": [1]})
    with pytest.raises(RuntimeErrorCode, match="object_key_invalid"):
        canonical_bytes({1: "bad"})
    assert canonical_bytes(Decimal("-0.0")) == b'"0"'
    assert thaw_value(freeze_value({"set": {1, 2}})) == {"set": [1, 2]}
