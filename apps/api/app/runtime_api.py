"""Minimal Phase 05 REST surface. Authentication is supplied by trusted Phase 03 composition."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from packages.domain.actions import ActionReceipt, InMemoryActionRepository
from packages.domain.authorization.policy import (
    Actor,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.ids import new_uuid7
from packages.runtime.src.lengeas_runtime.actions import plan_action
from packages.runtime.src.lengeas_runtime.context import ExecutionBudgets, ExecutionContext
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.events import OutboxRecord
from packages.runtime.src.lengeas_runtime.registry import core_registry
from packages.runtime.src.lengeas_runtime.serialization import digest
from packages.runtime.src.lengeas_runtime.state_paths import (
    StatePath,
    StatePathRegistry,
    path_token,
)
from packages.schemas.definition_validation import validate_bundle

PrincipalProvider = Callable[[], Awaitable[tuple[Actor, Any]]]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GameCreate(StrictModel):
    game_id: str = Field(min_length=3, max_length=64)
    definition: dict[str, Any]


class DraftCreate(StrictModel):
    definition: dict[str, Any]


class PlayerCreate(StrictModel):
    player_id: str = Field(min_length=3, max_length=64)


class ActionRequest(StrictModel):
    payload: dict[str, Any]
    expected_state_version: int = Field(ge=0)


class RuntimeApplication:
    def __init__(self) -> None:
        self.repository = InMemoryActionRepository()
        self.games: dict[tuple[str, str], dict[str, Any]] = {}
        self.drafts: dict[tuple[str, str], dict[str, Any]] = {}
        self.players: set[tuple[str, str, str]] = set()
        self.paths: dict[tuple[str, str], StatePathRegistry] = {}

    def register_state_paths(
        self, game_key: tuple[str, str], definition: dict[str, Any]
    ) -> StatePathRegistry:
        existing = self.paths.get(game_key)
        if existing is not None:
            return existing
        registry = StatePathRegistry()
        modules = definition.get("modules", [])
        namespaces: dict[str, str] = {}
        for module in modules:
            package_id = str(module.get("id", "core"))
            for namespace in module.get("state_namespaces", []):
                if namespace in namespaces:
                    raise RuntimeErrorCode("namespace_owned_by_multiple_modules")
                namespaces[str(namespace)] = package_id
        pending = [definition]
        seen_paths: set[str] = set()
        while pending:
            value = pending.pop()
            if isinstance(value, Mapping):
                if "namespace_id" in value and "segments" in value:
                    token = path_token(value)
                    namespace = str(value["namespace_id"])
                    owner = namespaces.get(namespace)
                    if owner is None:
                        raise RuntimeErrorCode("state_namespace_unowned")
                    if token not in seen_paths:
                        registry.register(
                            StatePath(
                                token,
                                namespace,
                                owner,
                                (int, str, bool, list, dict),
                                frozenset(
                                    module_id
                                    for module_id, module in (
                                        (str(item.get("id", "core")), item) for item in modules
                                    )
                                    if namespace in module.get("state_namespaces", [])
                                ),
                                frozenset({owner}),
                            )
                        )
                        seen_paths.add(token)
                pending.extend(value.values())
            elif isinstance(value, (list, tuple)):
                pending.extend(value)
        registry.freeze()
        self.paths[game_key] = registry
        return registry


def create_runtime_app(
    principal_provider: PrincipalProvider | None = None,
    runtime: RuntimeApplication | None = None,
    logical_clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    app = FastAPI(title="LenGeas Runtime API", version="1.0.0", openapi_version="3.1.0")
    app.state.runtime = runtime or RuntimeApplication()
    policy = PolicyDecisionService()

    async def principal() -> tuple[Actor, Any]:
        if principal_provider is None:
            raise HTTPException(status_code=401, detail={"code": "authentication_required"})
        return await principal_provider()

    def authorize(actor: Actor, environment: Any, action: str, resource: Resource) -> None:
        decision = policy.decide(PolicyRequest(actor, action, resource, environment))
        if not decision.allowed:
            raise HTTPException(status_code=403, detail={"code": decision.code})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {"api_version": "1.0.0", "engine_version": "1.0.0"}

    @app.post("/api/v1/games", status_code=201)
    async def create_game(
        body: GameCreate, identity: tuple[Actor, Any] = Depends(principal)
    ) -> dict[str, str]:
        actor, environment = identity
        authorize(actor, environment, "write", Resource("game", body.game_id, actor.studio_id))
        key = (str(actor.studio_id), body.game_id)
        if key in app.state.runtime.games:
            raise HTTPException(409, detail={"code": "game_exists"})
        app.state.runtime.games[key] = body.definition
        return {"game_id": body.game_id, "definition_digest": digest(body.definition)}

    @app.post("/api/v1/games/{game_id}/definitions/draft", status_code=201)
    async def create_draft(
        game_id: str, body: DraftCreate, identity: tuple[Actor, Any] = Depends(principal)
    ) -> dict[str, str]:
        actor, environment = identity
        permission = "draft_write" if actor.kind.value == "ai_agent" else "write"
        authorize(
            actor,
            environment,
            permission,
            Resource("definition", game_id, actor.studio_id, game_id),
        )
        draft_id = new_uuid7()
        app.state.runtime.drafts[(str(actor.studio_id), draft_id)] = body.definition
        return {"draft_id": draft_id, "game_id": game_id}

    @app.post("/api/v1/games/{game_id}/definitions/validate")
    async def validate_definition(
        game_id: str, body: DraftCreate, identity: tuple[Actor, Any] = Depends(principal)
    ) -> dict[str, Any]:
        actor, environment = identity
        authorize(actor, environment, "read", Resource("game", game_id, actor.studio_id, game_id))
        return validate_bundle(body.definition)

    @app.post("/api/v1/games/{game_id}/players", status_code=201)
    async def create_player(
        game_id: str, body: PlayerCreate, identity: tuple[Actor, Any] = Depends(principal)
    ) -> dict[str, str]:
        actor, environment = identity
        authorize(
            actor,
            environment,
            "write",
            Resource("player", body.player_id, actor.studio_id, game_id, actor.actor_id),
        )
        key = (str(actor.studio_id), game_id, body.player_id)
        if key in app.state.runtime.players:
            raise HTTPException(409, detail={"code": "player_exists"})
        app.state.runtime.players.add(key)
        app.state.runtime.repository.seed_state(key, {})
        return {"player_id": body.player_id, "game_id": game_id}

    @app.post("/api/v1/games/{game_id}/players/{player_id}/actions/{action_id}")
    async def execute_action(
        game_id: str,
        player_id: str,
        action_id: str,
        body: ActionRequest,
        idempotency_key: str = Header(alias="Idempotency-Key"),
        identity: tuple[Actor, Any] = Depends(principal),
    ) -> dict[str, Any]:
        actor, environment = identity
        authorize(
            actor,
            environment,
            "write",
            Resource("player", player_id, actor.studio_id, game_id, actor.actor_id),
        )
        key = (str(actor.studio_id), game_id, player_id)
        if key not in app.state.runtime.players:
            raise HTTPException(404, detail={"code": "player_not_found"})
        current = app.state.runtime.repository.state(key)
        if current is None:
            raise HTTPException(404, detail={"code": "state_not_found"})
        definition = app.state.runtime.games.get((str(actor.studio_id), game_id), {})
        documents = definition.get("documents", [])
        action = next(
            (
                item
                for item in documents
                if isinstance(item, Mapping) and item.get("id") == action_id
            ),
            None,
        )
        if action is None:
            raise HTTPException(404, detail={"code": "action_not_found"})
        owners = [
            str(module.get("id", "core"))
            for module in definition.get("modules", [])
            if action_id in module.get("registered_actions", [])
        ]
        if len(owners) > 1:
            raise HTTPException(422, detail={"code": "action_owner_invalid"})
        package_id = owners[0] if owners else "core"
        owner_module: Mapping[str, Any] = next(
            (module for module in definition.get("modules", []) if module.get("id") == package_id),
            {},
        )
        namespaces = frozenset(str(value) for value in owner_module.get("state_namespaces", []))
        try:
            path_registry = app.state.runtime.register_state_paths(
                (str(actor.studio_id), game_id), definition
            )
            now = logical_clock() if logical_clock is not None else datetime.now(UTC)
            seed = int.from_bytes(
                hashlib.sha256(
                    f"{actor.actor_id}\0{game_id}\0{player_id}\0{action_id}\0{idempotency_key}".encode()
                ).digest()[:16],
                "big",
            )
            context = ExecutionContext(
                "1.0.0",
                digest(definition),
                (),
                current[0],
                action_id,
                now,
                seed,
                (),
                "en",
                actor.actor_id,
                str(actor.studio_id),
                game_id,
                player_id,
                namespaces,
                namespaces,
                ExecutionBudgets(),
            )
            plan = plan_action(
                action,
                body.payload,
                current[1],
                context=context,
                path_registry=path_registry,
                handler_registry=core_registry(),
                package_id=package_id,
                timer_definitions={
                    str(item.get("id")): item
                    for item in documents
                    if isinstance(item, Mapping) and "duration_formula" in item
                },
            )
            if not plan.allowed:
                raise HTTPException(
                    409,
                    detail={"code": "condition_failed", "explanation": plan.explanation.as_dict()},
                )
            input_hash = hashlib.sha256(
                __import__("json")
                .dumps(body.payload, sort_keys=True, separators=(",", ":"))
                .encode()
            ).hexdigest()
            receipt_id = new_uuid7()
            event_records = tuple(OutboxRecord(new_uuid7(), event) for event in plan.events)
            receipt = ActionReceipt(
                receipt_id,
                actor.actor_id,
                str(actor.studio_id),
                game_id,
                player_id,
                action_id,
                input_hash,
                context.definition_digest,
                context.engine_version,
                current[0],
                current[0] + 1,
                "",
                context.logical_time.isoformat(),
                context.seed,
                "committed",
                plan.explanation.as_dict(),
                tuple(record.event_id for record in event_records),
            )
            fingerprint = hashlib.sha256(
                f"{action_id}\0{body.expected_state_version}\0{input_hash}".encode()
            ).hexdigest()
            committed = app.state.runtime.repository.commit_action(
                state_key=key,
                expected_version=body.expected_state_version,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                actor_id=actor.actor_id,
                plan=plan,
                receipt=receipt,
                outbox=event_records,
            )
            return {
                "receipt_id": committed.receipt_id,
                "status": committed.status,
                "state_version": committed.state_version,
                "state_digest": committed.state_digest,
                "definition_digest": committed.definition_digest,
                "event_ids": committed.event_ids,
            }
        except RuntimeErrorCode as error:
            code = 409 if error.code in {"state_conflict", "idempotency_conflict"} else 422
            raise HTTPException(code, detail={"code": error.code}) from error

    @app.get("/api/v1/games/{game_id}/players/{player_id}/receipts/{receipt_id}")
    async def read_receipt(
        game_id: str,
        player_id: str,
        receipt_id: str,
        identity: tuple[Actor, Any] = Depends(principal),
    ) -> Any:
        actor, environment = identity
        authorize(
            actor,
            environment,
            "read",
            Resource("player", player_id, actor.studio_id, game_id, actor.actor_id),
        )
        receipt = app.state.runtime.repository.receipt(
            (str(actor.studio_id), game_id, player_id), receipt_id
        )
        if receipt is None:
            raise HTTPException(404, detail={"code": "receipt_not_found"})
        return {field: getattr(receipt, field) for field in receipt.__dataclass_fields__}

    @app.get("/api/v1/games/{game_id}/players/{player_id}/state")
    async def read_state(
        game_id: str, player_id: str, identity: tuple[Actor, Any] = Depends(principal)
    ) -> dict[str, Any]:
        actor, environment = identity
        authorize(
            actor,
            environment,
            "read",
            Resource("player", player_id, actor.studio_id, game_id, actor.actor_id),
        )
        state = app.state.runtime.repository.state((str(actor.studio_id), game_id, player_id))
        if state is None:
            raise HTTPException(404, detail={"code": "state_not_found"})
        return {"state_version": state[0], "state": state[1], "state_digest": digest(state[1])}

    return app
