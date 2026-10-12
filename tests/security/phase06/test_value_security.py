from __future__ import annotations

import asyncio

import pytest

from packages.domain.economy import EconomyAction, EconomyError, InMemoryEconomyActionService
from packages.domain.inventory import (
    InMemoryInventoryRepository,
    InventoryError,
    InventoryScope,
    ItemDefinition,
)
from packages.domain.player_state import InMemoryPlayerStateRepository, PlayerStateScope, StateError
from packages.domain.providers.store_receipts import ProviderError


def test_state_patch_rejects_database_operators_and_nan_payloads() -> None:
    repository = InMemoryPlayerStateRepository()
    scope = PlayerStateScope("studio", "game", "player", "profile")
    with pytest.raises(StateError, match="invalid_state_path"):
        asyncio.run(repository.patch(scope, "state", 0, {"$where": "true"}))
    with pytest.raises(StateError, match="state_patch_not_canonical_json"):
        asyncio.run(repository.patch(scope, "state", 0, {"balance": float("nan")}))


def test_idempotency_payload_conflict_cannot_replay_a_different_reward() -> None:
    service = InMemoryEconomyActionService()
    common = dict(
        studio_id="s",
        game_id="g",
        player_id="p",
        actor_id="a",
        action_id="claim",
        idempotency_key="same",
        definition_digest="d",
    )
    service.execute(**common, action=EconomyAction(grants={"coin": 1}))
    with pytest.raises(EconomyError, match="idempotency_conflict"):
        service.execute(**common, action=EconomyAction(grants={"coin": 1_000_000}))
    assert service.ledger.balance("player:p:coin", "coin") == 1


def test_inventory_duplicate_claim_cannot_cross_scope_or_change_item_payload() -> None:
    repository = InMemoryInventoryRepository()
    owner = InventoryScope("s", "g", "p1", "profile1", "bag")
    other = InventoryScope("s", "g", "p2", "profile2", "bag")
    repository.create(owner, 2)
    repository.create(other, 2)
    item = ItemDefinition("token", True, max_stack=10)
    repository.grant(owner, item, 1, expected_version=0, idempotency_key="same")
    with pytest.raises(InventoryError, match="idempotency_conflict"):
        repository.grant(owner, item, 2, expected_version=0, idempotency_key="same")
    assert repository.read(other).stacks == ()


def test_store_adapters_reject_missing_trust_material_and_invalid_webhook() -> None:
    from packages.domain.providers.store_receipts import AppleStoreKitAdapter, GooglePlayAdapter

    with pytest.raises(ProviderError, match="apple_provider_configuration_invalid"):
        AppleStoreKitAdapter(
            base_url="http://insecure.example",
            bearer_token="x",
            bundle_id="game",
            trusted_root_certificates=(),
        )
    google = GooglePlayAdapter(
        package_name="game",
        access_token="token",
        expected_push_audience="aud",
        expected_push_email="publisher@example.com",
    )
    with pytest.raises(ProviderError, match="google_webhook_authentication_required"):
        asyncio.run(google.verify_webhook("", {"message": {}}))
