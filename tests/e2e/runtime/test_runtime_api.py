from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.app.runtime_api import create_runtime_app
from packages.domain.authorization.policy import Actor, ActorKind
from packages.domain.tenancy.models import Environment, MembershipRole


def test_runtime_api_authorization_and_action_lifecycle() -> None:
    actor = Actor(
        "owner-1",
        ActorKind.ACCOUNT,
        "studio-1",
        frozenset({MembershipRole.DEVELOPER}),
        game_ids=frozenset({"game-1"}),
        environments=frozenset({Environment.TESTING}),
    )

    async def principal() -> tuple[Actor, Environment]:
        return actor, Environment.TESTING

    action_definition = {"id": "act_test", "input_schema": {"type": "object"}}
    client = TestClient(
        create_runtime_app(principal, logical_clock=lambda: datetime(2030, 1, 1, tzinfo=UTC))
    )
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/version").json()["engine_version"] == "1.0.0"
    created = client.post(
        "/api/v1/games",
        json={"game_id": "game-1", "definition": {"documents": [action_definition]}},
    )
    assert created.status_code == 201
    draft = client.post(
        "/api/v1/games/game-1/definitions/draft", json={"definition": {"draft": True}}
    )
    assert draft.status_code == 201
    validation = client.post("/api/v1/games/game-1/definitions/validate", json={"definition": {}})
    assert validation.status_code == 200
    player = client.post("/api/v1/games/game-1/players", json={"player_id": "player-1"})
    assert player.status_code == 201
    action = client.post(
        "/api/v1/games/game-1/players/player-1/actions/act_test",
        headers={"Idempotency-Key": "idem-1"},
        json={"payload": {}, "expected_state_version": 0},
    )
    assert action.status_code == 200, action.text
    result = action.json()
    assert result["state_version"] == 1
    receipt = client.get(f"/api/v1/games/game-1/players/player-1/receipts/{result['receipt_id']}")
    state = client.get("/api/v1/games/game-1/players/player-1/state")
    assert receipt.status_code == state.status_code == 200
    assert state.json()["state_version"] == 1
    replay = client.post(
        "/api/v1/games/game-1/players/player-1/actions/act_test",
        headers={"Idempotency-Key": "idem-1"},
        json={"payload": {}, "expected_state_version": 0},
    )
    assert replay.json()["receipt_id"] == result["receipt_id"]
    stale = client.post(
        "/api/v1/games/game-1/players/player-1/actions/act_test",
        headers={"Idempotency-Key": "idem-stale"},
        json={"payload": {}, "expected_state_version": 0},
    )
    assert stale.status_code == 409
    conflict = client.post(
        "/api/v1/games/game-1/players/player-1/actions/act_test",
        headers={"Idempotency-Key": "idem-1"},
        json={"payload": {"different": True}, "expected_state_version": 0},
    )
    assert conflict.status_code == 409
    injected_definition = client.post(
        "/api/v1/games/game-1/players/player-1/actions/act_test",
        headers={"Idempotency-Key": "idem-2"},
        json={"action": {"id": "act_other"}, "payload": {}, "expected_state_version": 1},
    )
    assert injected_definition.status_code == 422


def test_runtime_api_fails_closed_without_trusted_principal() -> None:
    client = TestClient(create_runtime_app())
    response = client.post("/api/v1/games", json={"game_id": "game-1", "definition": {}})
    assert response.status_code == 401


def test_runtime_api_denies_viewer_mutations_and_cross_game_reads() -> None:
    actor = Actor(
        "viewer-1",
        ActorKind.ACCOUNT,
        "studio-1",
        frozenset({MembershipRole.VIEWER}),
        game_ids=frozenset({"game-1"}),
        environments=frozenset({Environment.TESTING}),
    )

    async def principal() -> tuple[Actor, Environment]:
        return actor, Environment.TESTING

    client = TestClient(create_runtime_app(principal))
    create = client.post("/api/v1/games", json={"game_id": "game-1", "definition": {}})
    assert create.status_code == 403
    read = client.get("/api/v1/games/game-2/players/player-1/state")
    assert read.status_code == 403
