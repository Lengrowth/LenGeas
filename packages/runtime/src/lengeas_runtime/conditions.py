"""Bounded pure condition evaluator with stable explanation trees."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.serialization import freeze_value, thaw_value
from packages.runtime.src.lengeas_runtime.state_paths import (
    StatePathRegistry,
    is_missing,
    path_token,
)

MAX_DEPTH = 32
MAX_NODES = 256


@dataclass(frozen=True, slots=True)
class Explanation:
    operator: str
    passed: bool
    code: str
    children: tuple[Explanation, ...] = ()
    actual: Any = None
    expected: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "actual", freeze_value(self.actual))
        object.__setattr__(self, "expected", freeze_value(self.expected))

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "operator": self.operator,
            "passed": self.passed,
            "code": self.code,
            "children": [child.as_dict() for child in self.children],
        }
        if self.actual is not None:
            result["actual"] = thaw_value(self.actual)
        if self.expected is not None:
            result["expected"] = thaw_value(self.expected)
        return result


def _operand(
    node: Any,
    state: Mapping[str, Any],
    registry: StatePathRegistry,
    package_id: str,
    logical_time: datetime,
) -> Any:
    if not isinstance(node, dict):
        return node
    operator = node.get("operator")
    if operator == "literal":
        return node.get("value")
    if operator in {"state", "state_path", "path"}:
        return registry.read(state, path_token(node.get("path", node.get("value", ""))), package_id)
    if operator == "logical_time":
        return logical_time
    if "path" in node and operator is None:
        return registry.read(state, path_token(node["path"]), package_id)
    raise RuntimeErrorCode("condition_operand_invalid")


def evaluate_condition(
    ast: Mapping[str, Any],
    state: Mapping[str, Any],
    registry: StatePathRegistry,
    package_id: str,
    logical_time: datetime,
    *,
    max_nodes: int = MAX_NODES,
    max_depth: int = MAX_DEPTH,
    predicates: Mapping[str, Callable[[Mapping[str, Any]], bool]] | None = None,
) -> Explanation:
    count = 0

    def visit(node: Any, depth: int) -> Explanation:
        nonlocal count
        count += 1
        if count > min(max_nodes, MAX_NODES) or depth > min(max_depth, MAX_DEPTH):
            raise RuntimeErrorCode("condition_budget_exceeded")
        if not isinstance(node, Mapping):
            raise RuntimeErrorCode("condition_ast_invalid")
        op = str(node.get("operator", ""))
        if "expression" in node:
            return visit(node["expression"], depth + 1)
        if op in {"all", "any"}:
            children_ast = node.get("conditions", node.get("args", []))
            if not isinstance(children_ast, (list, tuple)):
                raise RuntimeErrorCode("condition_ast_invalid")
            children = tuple(visit(child, depth + 1) for child in children_ast)
            passed = (
                all(child.passed for child in children)
                if op == "all"
                else any(child.passed for child in children)
            )
            return Explanation(
                op, passed, "condition_met" if passed else "condition_failed", children
            )
        if op == "not":
            child_ast = node.get("condition", node.get("arg"))
            if child_ast is None:
                args = node.get("args", [])
                child_ast = args[0] if isinstance(args, (list, tuple)) and len(args) == 1 else None
            child = visit(child_ast, depth + 1)
            return Explanation(
                op,
                not child.passed,
                "condition_met" if not child.passed else "condition_failed",
                (child,),
            )
        if op in {"exists", "elapsed_at_least"}:
            path = path_token(node.get("path", ""))
            try:
                actual = registry.read(state, path, package_id)
            except RuntimeErrorCode as error:
                if error.code == "state_path_missing" and op == "exists":
                    return Explanation(op, False, "state_absent")
                raise
            if op == "exists":
                passed = not is_missing(actual)
            else:
                if not isinstance(actual, datetime) or actual.tzinfo is None:
                    raise RuntimeErrorCode("condition_timestamp_invalid")
                duration_seconds = node.get("duration_seconds")
                if not isinstance(duration_seconds, int) or isinstance(duration_seconds, bool):
                    raise RuntimeErrorCode("condition_duration_invalid")
                passed = (logical_time - actual).total_seconds() >= duration_seconds
            return Explanation(
                op, passed, "condition_met" if passed else "condition_failed", actual=actual
            )
        if op in {"before", "after"}:
            expected = node.get("at")
            if not isinstance(expected, str):
                raise RuntimeErrorCode("condition_timestamp_invalid")
            try:
                expected_time = datetime.fromisoformat(expected.replace("Z", "+00:00"))
            except ValueError as error:
                raise RuntimeErrorCode("condition_timestamp_invalid") from error
            if expected_time.tzinfo is None:
                raise RuntimeErrorCode("condition_timestamp_invalid")
            passed = (
                logical_time < expected_time if op == "before" else logical_time > expected_time
            )
            return Explanation(
                op,
                passed,
                "condition_met" if passed else "condition_failed",
                actual=logical_time,
                expected=expected_time,
            )
        if op == "predicate":
            name = str(node.get("name", ""))
            handler = (predicates or {}).get(name)
            arguments = node.get("arguments", {})
            if handler is None:
                raise RuntimeErrorCode("condition_predicate_unregistered")
            if not isinstance(arguments, Mapping):
                raise RuntimeErrorCode("condition_ast_invalid")
            passed = bool(handler(arguments))
            return Explanation(op, passed, "condition_met" if passed else "condition_failed")
        left = _operand(
            node.get("left", node.get("value", node.get("a"))),
            state,
            registry,
            package_id,
            logical_time,
        )
        right = (
            _operand(node.get("right", node.get("b")), state, registry, package_id, logical_time)
            if op != "in"
            else None
        )
        if is_missing(left) or (op != "in" and is_missing(right)):
            raise RuntimeErrorCode("condition_operand_missing")
        if (
            op != "in"
            and type(left) is not type(right)
            and not (
                isinstance(left, int)
                and not isinstance(left, bool)
                and isinstance(right, int)
                and not isinstance(right, bool)
            )
        ):
            raise RuntimeErrorCode("condition_type_mismatch")
        if op == "eq":
            passed = left == right
        elif op == "ne":
            passed = left != right
        elif op == "lt":
            passed = left < right
        elif op == "lte":
            passed = left <= right
        elif op == "gt":
            passed = left > right
        elif op == "gte":
            passed = left >= right
        elif op == "in":
            left = _operand(node.get("value"), state, registry, package_id, logical_time)
            values = node.get("values")
            if not isinstance(values, (list, tuple)):
                raise RuntimeErrorCode("condition_ast_invalid")
            resolved = [
                _operand(value, state, registry, package_id, logical_time) for value in values
            ]
            passed = left in resolved
        else:
            raise RuntimeErrorCode("condition_operator_unknown")
        return Explanation(
            op,
            bool(passed),
            "condition_met" if passed else "condition_failed",
            actual=left,
            expected=right,
        )

    return visit(ast, 1)
