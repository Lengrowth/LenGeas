"""Translate trusted Phase 05 resource plans into conserved Phase 06 ledger actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from packages.domain.economy import EconomyAction, EconomyError
from packages.runtime.src.lengeas_runtime.actions import ActionPlan
from packages.runtime.src.lengeas_runtime.serialization import thaw_value


@dataclass(frozen=True, slots=True)
class ItemRewardIntent:
    item_id: str
    quantity: int
    attributes: Mapping[str, Any]


def _amount(value: Any) -> int:
    expanded = thaw_value(value)
    if isinstance(expanded, bool) or not isinstance(expanded, int) or expanded < 0:
        raise EconomyError("runtime_resource_amount_invalid")
    return int(expanded)


def economy_action_from_runtime_plan(plan: ActionPlan) -> EconomyAction:
    """Accept only server-computed resource costs and resource reward grants.

    Arbitrary state effects and non-resource rewards need their atomic domain
    handler and cannot be silently converted into a client-controlled ledger
    posting.
    """
    action, item_rewards = runtime_economy_contributions(plan)
    if item_rewards:
        raise EconomyError("runtime_reward_requires_domain_handler")
    return action


def runtime_economy_contributions(
    plan: ActionPlan,
) -> tuple[EconomyAction, tuple[ItemRewardIntent, ...]]:
    """Return resource postings and separately typed item reward intents."""
    if not plan.allowed:
        raise EconomyError("runtime_action_denied")
    costs: dict[str, int] = {}
    for operation in plan.costs:
        asset = _resource_path(operation.path)
        if operation.kind != "decrement":
            raise EconomyError("runtime_cost_operation_invalid")
        costs[asset] = costs.get(asset, 0) + _amount(operation.value)
    grants: dict[str, int] = {}
    item_rewards: list[ItemRewardIntent] = []
    for operation in plan.rewards:
        if operation.kind == "grant_item":
            payload = thaw_value(operation.value)
            if not isinstance(payload, Mapping):
                raise EconomyError("runtime_reward_payload_invalid")
            target = payload.get("target")
            if not isinstance(target, Mapping) or target.get("kind") != "item":
                raise EconomyError("runtime_item_target_invalid")
            item_id = str(target.get("id", ""))
            if not item_id:
                raise EconomyError("runtime_item_target_invalid")
            item_rewards.append(
                ItemRewardIntent(
                    item_id,
                    _amount(payload.get("quantity", 1)),
                    payload.get("attributes", {})
                    if isinstance(payload.get("attributes", {}), Mapping)
                    else {},
                )
            )
            continue
        if operation.kind != "grant_resource":
            raise EconomyError("runtime_reward_requires_domain_handler")
        payload = thaw_value(operation.value)
        if not isinstance(payload, Mapping):
            raise EconomyError("runtime_reward_payload_invalid")
        target = payload.get("target")
        if not isinstance(target, Mapping) or target.get("kind") != "resource":
            raise EconomyError("runtime_resource_target_invalid")
        asset = str(target.get("id", ""))
        if not asset:
            raise EconomyError("runtime_resource_target_invalid")
        grants[asset] = grants.get(asset, 0) + _amount(payload.get("quantity", 0))
    if plan.effects:
        if any(
            operation.path and operation.path.startswith("resource.") for operation in plan.effects
        ):
            raise EconomyError("runtime_resource_effect_must_use_reward_or_cost")
        raise EconomyError("runtime_effect_requires_atomic_effect_handler")
    return EconomyAction(costs=costs, grants=grants), tuple(item_rewards)


def _resource_path(path: str | None) -> str:
    if path is None:
        raise EconomyError("runtime_cost_target_invalid")
    segments = path.split(".")
    if len(segments) != 3 or segments[0] != "resource" or segments[2] != "balance":
        raise EconomyError("runtime_cost_target_invalid")
    return segments[1]
