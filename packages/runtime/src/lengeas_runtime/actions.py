"""Immutable definition-driven action planning."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from packages.runtime.src.lengeas_runtime.conditions import Explanation, evaluate_condition
from packages.runtime.src.lengeas_runtime.context import ExecutionContext
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.events import EventDraft, event_draft
from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula
from packages.runtime.src.lengeas_runtime.registry import HandlerRegistry, core_registry
from packages.runtime.src.lengeas_runtime.serialization import canonical_bytes, freeze_value
from packages.runtime.src.lengeas_runtime.state_paths import StatePathRegistry, path_token
from packages.runtime.src.lengeas_runtime.timers import TimerPlan, plan_timer


@dataclass(frozen=True, slots=True)
class PlannedOperation:
    kind: str
    package_id: str
    path: str | None
    value: Any
    ordinal: int


@dataclass(frozen=True, slots=True)
class ActionPlan:
    action_id: str
    input_digest: str
    allowed: bool
    explanation: Explanation
    costs: tuple[PlannedOperation, ...]
    effects: tuple[PlannedOperation, ...]
    rewards: tuple[PlannedOperation, ...]
    timers: tuple[TimerPlan, ...]
    events: tuple[EventDraft, ...]
    operation_count: int

    @property
    def operations(self) -> tuple[PlannedOperation, ...]:
        return self.costs + self.effects + self.rewards


def validate_input(payload: Any, schema: Mapping[str, Any]) -> None:
    def validate(value: Any, rule: Mapping[str, Any], depth: int) -> None:
        if depth > 32:
            raise RuntimeErrorCode("action_input_depth_exceeded")
        expected = str(rule["type"]) if "type" in rule else None
        validators = {
            "object": lambda item: isinstance(item, Mapping),
            "array": lambda item: isinstance(item, (list, tuple)),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, Decimal)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        valid = validators.get(expected) if expected is not None else None
        if valid is not None and not valid(value):
            raise RuntimeErrorCode("action_input_type_invalid")
        if "const" in rule and value != rule["const"]:
            raise RuntimeErrorCode("action_input_const_invalid")
        if "enum" in rule and value not in rule["enum"]:
            raise RuntimeErrorCode("action_input_enum_invalid")
        if isinstance(value, Mapping):
            properties = rule.get("properties", {})
            if not isinstance(properties, Mapping):
                raise RuntimeErrorCode("action_input_schema_invalid")
            if any(name not in value for name in rule.get("required", [])):
                raise RuntimeErrorCode("action_input_required")
            if rule.get("additionalProperties") is False and set(value) - set(properties):
                raise RuntimeErrorCode("action_input_unknown_field")
            if len(value) > 256:
                raise RuntimeErrorCode("action_input_limit_exceeded")
            for name, item in value.items():
                if name in properties:
                    nested = properties[name]
                    if not isinstance(nested, Mapping):
                        raise RuntimeErrorCode("action_input_schema_invalid")
                    validate(item, nested, depth + 1)
        elif isinstance(value, (list, tuple)):
            if len(value) > int(rule.get("maxItems", 256)):
                raise RuntimeErrorCode("action_input_limit_exceeded")
            nested = rule.get("items")
            if nested is not None:
                if not isinstance(nested, Mapping):
                    raise RuntimeErrorCode("action_input_schema_invalid")
                for item in value:
                    validate(item, nested, depth + 1)
        elif isinstance(value, str):
            if len(value.encode()) > min(4096, int(rule.get("maxLength", 4096))):
                raise RuntimeErrorCode("action_input_limit_exceeded")
            if len(value) < int(rule.get("minLength", 0)):
                raise RuntimeErrorCode("action_input_length_invalid")
            if "pattern" in rule and not re.fullmatch(str(rule["pattern"]), value):
                raise RuntimeErrorCode("action_input_pattern_invalid")
        elif isinstance(value, (int, Decimal)) and not isinstance(value, bool):
            if value < rule.get("minimum", value) or value > rule.get("maximum", value):
                raise RuntimeErrorCode("action_input_range_invalid")

    validate(payload, schema, 0)


def _target_path(value: Any) -> str:
    if isinstance(value, Mapping) and "namespace_id" in value:
        return path_token(value)
    if (
        isinstance(value, Mapping)
        and isinstance(value.get("kind"), str)
        and isinstance(value.get("id"), str)
    ):
        suffix = "balance" if value["kind"] == "resource" else "value"
        return f"{value['kind']}.{value['id']}.{suffix}"
    if isinstance(value, str):
        return value
    raise RuntimeErrorCode("state_path_invalid")


def _formula(
    specification: Any,
    variables: Mapping[str, Any],
    budget: int,
    condition: Callable[[Mapping[str, Any]], bool],
) -> Decimal:
    if isinstance(specification, Mapping) and "expression" in specification:
        declared = frozenset(str(item) for item in specification.get("variables", []))
        return evaluate_formula(
            specification,
            variables,
            allowed_variables=declared,
            max_operations=budget,
            condition=condition,
        )
    if isinstance(specification, Mapping):
        return evaluate_formula(
            specification,
            variables,
            allowed_variables=frozenset(variables),
            max_operations=budget,
            condition=condition,
        )
    return evaluate_formula(
        {"operator": "literal", "value": specification},
        variables,
        allowed_variables=frozenset(variables),
        max_operations=budget,
        condition=condition,
    )


def _coerce_numeric(value: Decimal, value_type: type | tuple[type, ...]) -> Any:
    if value_type is int:
        if value != value.to_integral_value():
            raise RuntimeErrorCode("numeric_scale_loss")
        return int(value)
    if value_type is str:
        return format(value, "f")
    return value


def plan_action(
    action: Mapping[str, Any],
    payload: Any,
    state: Mapping[str, Any],
    *,
    context: ExecutionContext,
    path_registry: StatePathRegistry,
    handler_registry: HandlerRegistry | None = None,
    package_id: str = "core",
    predicates: Mapping[str, Callable[[Mapping[str, Any]], bool]] | None = None,
    timer_definitions: Mapping[str, Mapping[str, Any]] | None = None,
) -> ActionPlan:
    validate_input(payload, action.get("input_schema", {"type": "object"}))
    registry = handler_registry or core_registry()
    if not registry.frozen:
        raise RuntimeErrorCode("registry_must_be_frozen")
    variables = payload if isinstance(payload, Mapping) else {}
    input_digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()

    def check_condition(ast: Mapping[str, Any]) -> Explanation:
        return evaluate_condition(
            ast,
            state,
            path_registry,
            package_id,
            context.logical_time,
            max_nodes=context.budgets.condition_nodes,
            predicates=predicates,
        )

    conditions = action.get("conditions", [])
    if not isinstance(conditions, (list, tuple)):
        raise RuntimeErrorCode("condition_ast_invalid")
    explanation = check_condition({"operator": "all", "args": conditions})
    if not explanation.passed:
        return ActionPlan(
            str(action.get("id", context.action_id)),
            input_digest,
            False,
            explanation,
            (),
            (),
            (),
            (),
            (),
            len(conditions),
        )

    costs: list[PlannedOperation] = []
    effects: list[PlannedOperation] = []
    rewards: list[PlannedOperation] = []
    timers: list[TimerPlan] = []
    events: list[EventDraft] = []
    ordinal = len(conditions)

    for cost in action.get("costs", []):
        owner = str(cost.get("owner", package_id))
        path = _target_path(cost.get("path", cost.get("target")))
        registered = path_registry.resolve(path, owner, write=True)
        if (
            registered.namespace not in context.readable_namespaces
            or registered.namespace not in context.writable_namespaces
        ):
            raise RuntimeErrorCode("namespace_access_denied")
        quantity = _formula(
            cost.get("quantity", cost.get("amount", 0)),
            variables,
            context.budgets.formula_operations,
            lambda ast: check_condition(ast).passed,
        )
        current = path_registry.read(state, path, owner)
        available = Decimal(str(current))
        insufficiency = cost.get("insufficiency", cost.get("on_insufficient", "reject"))
        if available < quantity:
            if insufficiency == "partial":
                quantity = max(available, Decimal(0))
            else:
                denial = Explanation(
                    "cost", False, "insufficient_cost", actual=current, expected=quantity
                )
                return ActionPlan(
                    str(action.get("id", context.action_id)),
                    input_digest,
                    False,
                    denial,
                    (),
                    (),
                    (),
                    (),
                    (),
                    ordinal,
                )
        quantity = _coerce_numeric(quantity, registered.value_type)
        costs.append(PlannedOperation("decrement", owner, path, quantity, ordinal))
        ordinal += 1

    def expand(raw: Mapping[str, Any], target: list[PlannedOperation]) -> None:
        nonlocal ordinal
        operation = str(raw.get("operation", raw.get("type", "")))
        package = str(raw.get("owner", package_id))
        generated = registry.effect(operation, package, state, raw)
        for entry in generated:
            raw_path = entry.get("path")
            if (
                raw_path is None
                and entry.get("target") is not None
                and operation not in {"start_timer", "cancel_timer", "emit_event"}
            ):
                raw_path = _target_path(entry["target"])
            path = path_token(raw_path) if raw_path is not None else None
            if path is not None:
                registered = path_registry.resolve(path, package, write=True)
                if registered.namespace not in context.writable_namespaces:
                    raise RuntimeErrorCode("namespace_access_denied")
            value = entry.get("value", entry.get("amount", entry.get("payload")))
            if (
                isinstance(value, Mapping)
                and "operator" in value
                or isinstance(value, Mapping)
                and "expression" in value
            ):
                value = _formula(
                    value,
                    variables,
                    context.budgets.formula_operations,
                    lambda ast: check_condition(ast).passed,
                )
            if path is not None and isinstance(value, Decimal):
                path_definition = path_registry.resolve(path, package, write=True)
                value = _coerce_numeric(value, path_definition.value_type)
            target.append(PlannedOperation(operation, package, path, freeze_value(value), ordinal))
            if operation == "start_timer":
                timer_id = str(entry.get("timer_id", entry.get("target", {}).get("id", "")))
                timer_definition = (timer_definitions or {}).get(timer_id)
                authority = str(entry.get("authority", "server"))
                duration_value = entry.get("duration_ms", 0)
                if timer_definition is not None:
                    authority = str(timer_definition.get("authority", authority))
                    duration_formula = timer_definition.get("duration_formula")
                    if duration_formula is not None:
                        duration_value = _formula(
                            duration_formula,
                            variables,
                            context.budgets.formula_operations,
                            lambda ast: check_condition(ast).passed,
                        )
                duration = int(duration_value)
                timers.append(
                    plan_timer(
                        timer_id,
                        context.logical_time,
                        duration,
                        authority,
                        context.definition_digest,
                    )
                )
            if operation == "emit_event":
                event_value = entry.get("value", {})
                if not isinstance(event_value, Mapping):
                    event_value = {}
                events.append(
                    event_draft(
                        len(events),
                        str(
                            event_value.get(
                                "event_type", entry.get("event_type", "runtime.changed.v1")
                            )
                        ),
                        context.logical_time,
                        producer="runtime",
                        studio_id=context.studio_id,
                        game_id=context.game_id,
                        player_id=context.player_id,
                        definition_digest=context.definition_digest,
                        correlation_id=str(
                            event_value.get("correlation_id", entry.get("correlation_id", ""))
                        ),
                        causation_id=event_value.get("causation_id", entry.get("causation_id")),
                        payload=event_value.get("payload", entry.get("payload", {})),
                    )
                )
            ordinal += 1

    for effect in action.get("effects", []):
        expand(effect, effects)
    for reward in action.get("rewards", []):
        entries = reward.get("entries", [reward])
        if not isinstance(entries, (list, tuple)):
            raise RuntimeErrorCode("reward_entries_invalid")
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise RuntimeErrorCode("reward_entries_invalid")
            reward_kind = str(entry.get("type", entry.get("kind", "resource")))
            expanded = registry.reward(
                reward_kind, str(reward.get("owner", package_id)), {**entry, "entries": [entry]}
            )
            for generated in expanded:
                rewards.append(
                    PlannedOperation(
                        f"grant_{reward_kind}",
                        str(reward.get("owner", package_id)),
                        None,
                        freeze_value(generated),
                        ordinal,
                    )
                )
                ordinal += 1

    emitted = action.get("emitted_events", [])
    if not isinstance(emitted, (list, tuple)):
        raise RuntimeErrorCode("event_definition_invalid")
    for event in emitted:
        event_type = str(event.get("type", event) if isinstance(event, Mapping) else event)
        events.append(
            event_draft(
                len(events),
                event_type,
                context.logical_time,
                producer="runtime",
                studio_id=context.studio_id,
                game_id=context.game_id,
                player_id=context.player_id,
                definition_digest=context.definition_digest,
                correlation_id="",
                causation_id=None,
                payload={},
            )
        )

    operation_count = ordinal + len(events)
    if len(effects) + len(rewards) > context.budgets.effects:
        raise RuntimeErrorCode("effect_budget_exceeded")
    if len(events) > context.budgets.events:
        raise RuntimeErrorCode("event_budget_exceeded")
    patch_bytes = canonical_bytes(
        [
            {"kind": item.kind, "path": item.path, "value": item.value}
            for item in costs + effects + rewards
        ]
    )
    if len(patch_bytes) > context.budgets.state_patch_bytes:
        raise RuntimeErrorCode("state_patch_budget_exceeded")
    return ActionPlan(
        str(action.get("id", context.action_id)),
        input_digest,
        True,
        explanation,
        tuple(costs),
        tuple(effects),
        tuple(rewards),
        tuple(timers),
        tuple(events),
        operation_count,
    )
