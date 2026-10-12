from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from packages.domain.economy import EconomyAction, InMemoryEconomyActionService


@given(
    grant=st.integers(min_value=1, max_value=10**9), spend=st.integers(min_value=1, max_value=10**9)
)
def test_grant_and_spend_conserve_every_resource(grant: int, spend: int) -> None:
    spend = min(spend, grant)
    service = InMemoryEconomyActionService()
    service.execute(
        studio_id="studio",
        game_id="fixture_game",
        player_id="player",
        actor_id="actor",
        action_id="grant",
        idempotency_key="grant",
        definition_digest="sha256:fixture",
        action=EconomyAction(grants={"coin": grant}),
    )
    service.execute(
        studio_id="studio",
        game_id="fixture_game",
        player_id="player",
        actor_id="actor",
        action_id="spend",
        idempotency_key="spend",
        definition_digest="sha256:fixture",
        action=EconomyAction(costs={"coin": spend}),
    )
    assert service.ledger.balance("player:player:coin", "coin") == grant - spend
    for transaction in service.ledger.transactions():
        assert sum(entry.amount for entry in transaction.entries if entry.asset_id == "coin") == 0


@given(
    amount=st.integers(min_value=3, max_value=10**9),
    multiplier=st.integers(min_value=1, max_value=8),
)
def test_integer_multiplier_has_no_fractional_value_or_float(amount: int, multiplier: int) -> None:
    service = InMemoryEconomyActionService()
    receipt = service.execute(
        studio_id="studio",
        game_id="fixture_game",
        player_id="player",
        actor_id="actor",
        action_id="reward",
        idempotency_key="reward",
        definition_digest="sha256:fixture",
        action=EconomyAction(grants={"shard": amount}, multipliers={"shard": (multiplier, 3)}),
    )
    assert receipt.balances["shard"] == amount * multiplier // 3
    assert isinstance(receipt.balances["shard"], int)
