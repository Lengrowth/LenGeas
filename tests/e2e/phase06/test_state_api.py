from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.state_economy_api import create_state_economy_router
from packages.domain.authorization.policy import Actor, ActorKind
from packages.domain.player_state import InMemoryPlayerStateRepository
from packages.domain.tenancy.models import Environment, MembershipRole


def test_authenticated_state_patch_and_projection() -> None:
    actor = Actor(
        "developer-1",
        ActorKind.ACCOUNT,
        "studio-1",
        roles=frozenset({MembershipRole.DEVELOPER}),
        game_ids=frozenset({"game-1"}),
        environments=frozenset({Environment.TESTING}),
    )

    async def trusted_identity() -> tuple[Actor, Environment]:
        return actor, Environment.TESTING

    app = FastAPI()
    app.include_router(
        create_state_economy_router(InMemoryPlayerStateRepository(), trusted_identity)
    )
    client = TestClient(app)
    root = "/api/v1/games/game-1/players/player-1"
    patched = client.patch(
        f"{root}/state/progression",
        json={
            "game_profile_id": "profile-1",
            "expected_version": 0,
            "patch": {"level": 4},
        },
    )
    assert patched.status_code == 200
    assert patched.json()["state_version"] == 1
    projected = client.get(f"{root}/state?game_profile_id=profile-1")
    assert projected.status_code == 200
    assert projected.json()["namespaces"]["progression"] == {"level": 4}


def test_unauthenticated_state_routes_fail_closed() -> None:
    async def unauthenticated() -> tuple[Actor, Environment]:
        raise RuntimeError("missing trusted identity")

    app = FastAPI()
    app.include_router(
        create_state_economy_router(InMemoryPlayerStateRepository(), unauthenticated)
    )
    response = TestClient(app).get(
        "/api/v1/games/game-1/players/player-1/state?game_profile_id=profile-1"
    )
    assert response.status_code == 401


def test_client_cannot_supply_reward_amounts() -> None:
    actor = Actor(
        "developer-1",
        ActorKind.ACCOUNT,
        "studio-1",
        roles=frozenset({MembershipRole.DEVELOPER}),
        game_ids=frozenset({"game-1"}),
        environments=frozenset({Environment.TESTING}),
    )

    async def trusted_identity() -> tuple[Actor, Environment]:
        return actor, Environment.TESTING

    app = FastAPI()
    app.include_router(
        create_state_economy_router(InMemoryPlayerStateRepository(), trusted_identity)
    )
    response = TestClient(app).post(
        "/api/v1/games/game-1/players/player-1/economy/actions",
        headers={"Idempotency-Key": "client-claim"},
        json={
            "action_id": "daily_reward",
            "game_profile_id": "profile-1",
            "expected_state_version": 0,
            "grants": {"coin": 999_999},
        },
    )
    assert response.status_code == 422
