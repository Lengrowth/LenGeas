"""Bounded numeric AST evaluator using Decimal and signed-64-bit bounds."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation, localcontext
from typing import Any

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode

MAX_OPERATIONS = 512
MAX_DEPTH = 32
MAX_INTEGER = 2**63 - 1
MIN_INTEGER = -(2**63)
MAX_SCALE = 9


def _number(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str, Decimal)):
        raise RuntimeErrorCode("formula_number_invalid")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise RuntimeErrorCode("formula_number_invalid") from error
    if not number.is_finite() or number < MIN_INTEGER or number > MAX_INTEGER:
        raise RuntimeErrorCode("numeric_overflow")
    exponent = number.as_tuple().exponent
    if isinstance(exponent, int) and max(0, -exponent) > MAX_SCALE:
        raise RuntimeErrorCode("numeric_scale_exceeded")
    return number


def evaluate_formula(
    ast: Mapping[str, Any],
    variables: Mapping[str, Any],
    *,
    allowed_variables: frozenset[str] | None = None,
    max_operations: int = MAX_OPERATIONS,
    max_depth: int = MAX_DEPTH,
    condition: Callable[[Mapping[str, Any]], bool] | None = None,
) -> Decimal:
    count = 0

    def visit(node: Any, depth: int) -> Decimal:
        nonlocal count
        count += 1
        if count > min(max_operations, MAX_OPERATIONS) or depth > min(max_depth, MAX_DEPTH):
            raise RuntimeErrorCode("formula_operation_budget_exceeded")
        if not isinstance(node, Mapping):
            raise RuntimeErrorCode("formula_ast_invalid")
        if "expression" in node:
            declared = frozenset(str(value) for value in node.get("variables", []))
            if allowed_variables is not None and not declared <= allowed_variables:
                raise RuntimeErrorCode("formula_variable_not_allowed")
            pending = [node["expression"]]
            while pending:
                current = pending.pop()
                if isinstance(current, Mapping):
                    if (
                        current.get("operator") == "variable"
                        and current.get("name") not in declared
                    ):
                        raise RuntimeErrorCode("formula_variable_not_allowed")
                    pending.extend(current.values())
                elif isinstance(current, (list, tuple)):
                    pending.extend(current)
            return visit(node["expression"], depth + 1)
        op = str(node.get("operator", ""))
        if op == "literal":
            return _number(node.get("value"))
        if op == "variable":
            name = str(node.get("name", ""))
            if allowed_variables is not None and name not in allowed_variables:
                raise RuntimeErrorCode("formula_variable_not_allowed")
            if name not in variables:
                raise RuntimeErrorCode("formula_variable_missing")
            return _number(variables[name])
        raw_args = node.get("args", [])
        if not isinstance(raw_args, (list, tuple)):
            raise RuntimeErrorCode("formula_ast_invalid")
        args = [visit(value, depth + 1) for value in raw_args]
        try:
            with localcontext() as context:
                context.prec = 40
                if op == "add" and args:
                    result = sum(args, Decimal(0))
                elif op == "subtract" and len(args) >= 2:
                    result = args[0]
                    for value in args[1:]:
                        result -= value
                elif op == "multiply" and args:
                    result = Decimal(1)
                    for value in args:
                        result *= value
                elif op == "divide" and len(args) >= 2:
                    result = args[0]
                    for value in args[1:]:
                        if value == 0:
                            raise RuntimeErrorCode("division_by_zero")
                        result /= value
                elif op == "min" and args:
                    result = min(args)
                elif op == "max" and args:
                    result = max(args)
                elif op == "clamp" and len(args) == 3:
                    if args[1] > args[2]:
                        raise RuntimeErrorCode("formula_range_invalid")
                    result = min(max(args[0], args[1]), args[2])
                elif op == "floor" and len(args) == 1:
                    result = args[0].to_integral_value(rounding=ROUND_FLOOR)
                elif op == "ceil" and len(args) == 1:
                    result = args[0].to_integral_value(rounding=ROUND_CEILING)
                elif op == "power_integer" and len(args) == 2:
                    if args[1] != args[1].to_integral_value() or abs(args[1]) > 16:
                        raise RuntimeErrorCode("formula_exponent_invalid")
                    if args[0] == 0 and args[1] < 0:
                        raise RuntimeErrorCode("division_by_zero")
                    result = args[0] ** int(args[1])
                elif op == "piecewise":
                    cases = node.get("cases", [])
                    default = node.get("fallback")
                    if not isinstance(cases, list):
                        raise RuntimeErrorCode("formula_ast_invalid")
                    if condition is None:
                        raise RuntimeErrorCode("formula_piecewise_condition_context_required")
                    selected = next(
                        (case.get("then") for case in cases if condition(case.get("when", {}))),
                        default,
                    )
                    if selected is None:
                        raise RuntimeErrorCode("formula_piecewise_no_match")
                    result = visit(selected, depth + 1)
                else:
                    raise RuntimeErrorCode("formula_operator_unknown")
        except (InvalidOperation, OverflowError, ZeroDivisionError) as error:
            raise RuntimeErrorCode("numeric_overflow") from error
        return _number(result)

    return visit(ast, 1)
