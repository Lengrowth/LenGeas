from datetime import UTC, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from packages.runtime.src.lengeas_runtime.conditions import evaluate_condition
from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula
from packages.runtime.src.lengeas_runtime.state_paths import StatePathRegistry


def literal(value: int) -> dict[str, object]:
    return {"operator": "literal", "value": value}


def evaluate_boolean(ast: dict[str, object]) -> bool:
    return evaluate_condition(
        ast, {}, StatePathRegistry(), "core", datetime(2030, 1, 1, tzinfo=UTC)
    ).passed


@given(
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
)
def test_add_is_commutative_for_bounded_integers(left: int, right: int) -> None:
    forward = evaluate_formula({"operator": "add", "args": [literal(left), literal(right)]}, {})
    reverse = evaluate_formula({"operator": "add", "args": [literal(right), literal(left)]}, {})
    assert forward == reverse == Decimal(left + right)


@given(st.integers(min_value=0, max_value=2**31 - 1))
def test_min_and_max_bounds(value: int) -> None:
    expr = {
        "operator": "clamp",
        "args": [
            {"operator": "literal", "value": value},
            {"operator": "literal", "value": 0},
            {"operator": "literal", "value": 100},
        ],
    }
    result = evaluate_formula(expr, {})
    assert Decimal(0) <= result <= Decimal(100)


@given(st.booleans(), st.booleans())
def test_boolean_all_and_any_are_order_independent(left: bool, right: bool) -> None:
    first = {"operator": "eq", "left": left, "right": True}
    second = {"operator": "eq", "left": right, "right": True}
    assert evaluate_boolean({"operator": "all", "args": [first, second]}) == (left and right)
    assert evaluate_boolean({"operator": "all", "args": [second, first]}) == (left and right)
    assert evaluate_boolean({"operator": "any", "args": [first, second]}) == (left or right)


@given(st.booleans())
def test_boolean_negation_is_an_involution(value: bool) -> None:
    expression = {"operator": "eq", "left": value, "right": True}
    negated = {"operator": "not", "args": [expression]}
    double_negated = {"operator": "not", "args": [negated]}
    assert evaluate_boolean(double_negated) is value
