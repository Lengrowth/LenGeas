"""Authenticated Phase 06 state/economy routes over an injected durable repository."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from packages.domain.authorization.policy import (
    Actor,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.economy import EconomyAction, EconomyError
from packages.domain.inventory import InventoryRewardGrant
from packages.domain.player_state import PlayerStateScope, StateError
from packages.domain.tenancy.models import Environment

TrustedIdentity = Callable[[], Awaitable[tuple[Actor, Environment]]]
EconomyPlanResolver = Callable[
    [Actor, str, str, str, Mapping[str, Any], int], Awaitable["EconomyPlan"]
]


@dataclass(frozen=True, slots=True)
class EconomyPlan:
    action: EconomyAction
    state_patch: Mapping[str, Any]
    definition_digest: str
    inventory_grants: tuple[InventoryRewardGrant, ...] = ()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatePatch(StrictModel):
    game_profile_id: str = Field(min_length=1, max_length=128)
    expected_version: int = Field(ge=0)
    patch: dict[str, Any]


class EconomyActionRequest(StrictModel):
    action_id: str = Field(min_length=1, max_length=128)
    game_profile_id: str = Field(min_length=1, max_length=128)
    expected_state_version: int = Field(ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


def create_state_economy_router(
    repository: Any,
    trusted_identity: TrustedIdentity,
    action_resolver: EconomyPlanResolver | None = None,
) -> APIRouter:
    """Create routes that require the Phase 03 trusted actor/environment provider."""
    router = APIRouter(prefix="/api/v1/games/{game_id}/players/{player_id}")
    policy = PolicyDecisionService()

    async def identity() -> tuple[Actor, Environment]:
        try:
            return await trusted_identity()
        except Exception as error:
            raise HTTPException(401, detail={"code": "authentication_required"}) from error

    def authorize(actor: Actor, environment: Environment, game_id: str, action: str) -> None:
        decision = policy.decide(
            PolicyRequest(
                actor,
                action,
                Resource("player_state", game_id, actor.studio_id, game_id),
                environment,
            )
        )
        if not decision.allowed:
            raise HTTPException(403, detail={"code": decision.code})

    @router.get("/state")
    async def project_state(
        game_id: str,
        player_id: str,
        game_profile_id: str,
        who: tuple[Actor, Environment] = Depends(identity),
    ) -> Mapping[str, Any]:
        actor, environment = who
        authorize(actor, environment, game_id, "read")
        scope = PlayerStateScope(str(actor.studio_id), game_id, player_id, game_profile_id)
        return cast(Mapping[str, Any], await repository.project(scope))

    @router.patch("/state/{namespace_id}")
    async def patch_state(
        game_id: str,
        player_id: str,
        namespace_id: str,
        body: StatePatch,
        who: tuple[Actor, Environment] = Depends(identity),
    ) -> Mapping[str, Any]:
        actor, environment = who
        authorize(actor, environment, game_id, "write")
        scope = PlayerStateScope(str(actor.studio_id), game_id, player_id, body.game_profile_id)
        try:
            result = await repository.patch(scope, namespace_id, body.expected_version, body.patch)
        except StateError as error:
            raise HTTPException(409, detail={"code": str(error)}) from error
        return {
            "namespace_id": result.namespace_id,
            "prior_state_version": result.prior_state_version,
            "state_version": result.state_version,
            "patch": dict(result.patch),
            "state_digest": result.state_digest,
            "updated_at": result.updated_at,
        }

    @router.post("/economy/actions", status_code=201)
    async def execute_economy_action(
        game_id: str,
        player_id: str,
        body: EconomyActionRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
        who: tuple[Actor, Environment] = Depends(identity),
    ) -> Mapping[str, Any]:
        actor, environment = who
        authorize(actor, environment, game_id, "write")
        if action_resolver is None:
            raise HTTPException(503, detail={"code": "economy_plan_unavailable"})
        try:
            plan = await action_resolver(
                actor,
                game_id,
                player_id,
                body.action_id,
                body.payload,
                body.expected_state_version,
            )
            response = await repository.execute_action(
                studio_id=str(actor.studio_id),
                game_id=game_id,
                player_id=player_id,
                game_profile_id=body.game_profile_id,
                actor_id=actor.actor_id,
                action_id=body.action_id,
                expected_state_version=body.expected_state_version,
                state_patch=dict(plan.state_patch),
                action=plan.action,
                idempotency_key=idempotency_key,
                definition_digest=plan.definition_digest,
                inventory_grants=plan.inventory_grants,
            )
            return cast(Mapping[str, Any], response)
        except EconomyError as error:
            code = str(error)
            status = (
                409
                if code in {"state_conflict", "idempotency_conflict", "insufficient_balance"}
                else 422
            )
            raise HTTPException(status, detail={"code": code}) from error

    return router
