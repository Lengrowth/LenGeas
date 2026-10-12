"""MongoDB cross-game approvals in game blueprints and durable delivery receipts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast

from pymongo.errors import DuplicateKeyError

from packages.domain.cross_game import CrossGameContract, CrossGameError, SourceEvent
from packages.domain.ids import new_uuid7


class MongoCrossGameRepository:
    """Uses only documented game_blueprints, action_receipts and outbox_events collections."""

    def __init__(self, database: Any) -> None:
        self.blueprints = database.game_blueprints
        self.receipts = database.action_receipts
        self.outbox = database.outbox_events
        self.client = database.client

    async def ensure_indexes(self) -> None:
        await self.receipts.create_index(
            [("record_type", 1), ("contract_id", 1), ("source_event_id", 1)],
            unique=True,
            partialFilterExpression={"record_type": "cross_game_delivery"},
            name="uq_cross_game_source_event_delivery",
        )
        await self.receipts.create_index(
            [("record_type", 1), ("contract_id", 1), ("source_player_id", 1)],
            partialFilterExpression={"record_type": "cross_game_delivery"},
            name="cross_game_player_delivery_limit",
        )
        await self.outbox.create_index("event_id", unique=True, name="uq_outbox_event_id")

    @staticmethod
    def _document(contract: CrossGameContract) -> dict[str, Any]:
        return {
            "contract_id": contract.contract_id,
            "studio_id": contract.studio_id,
            "source_game_id": contract.source_game_id,
            "target_game_id": contract.target_game_id,
            "event_types": sorted(contract.event_types),
            "target_action_id": contract.target_action_id,
            "payload_fields": sorted(contract.payload_fields),
            "reward_limits": dict(contract.reward_limits),
            "max_deliveries_per_player": contract.max_deliveries_per_player,
            "status": contract.status,
            "expires_at": contract.expires_at,
            "revoked_at": contract.revoked_at,
        }

    async def approve(self, contract: CrossGameContract) -> None:
        if contract.status != "approved":
            raise CrossGameError("contract_not_approved")
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                # Touch every blueprint in the studio so concurrent edge approvals
                # conflict on a shared write and the cycle check is serialized.
                await self.blueprints.update_many(
                    {"studio_id": contract.studio_id},
                    {"$inc": {"contract_approval_version": 1}},
                    session=session,
                )
                source = await self.blueprints.find_one(
                    {"studio_id": contract.studio_id, "game_id": contract.source_game_id},
                    session=session,
                )
                target = await self.blueprints.find_one(
                    {"studio_id": contract.studio_id, "game_id": contract.target_game_id},
                    session=session,
                )
                if source is None:
                    raise CrossGameError("source_game_not_found")
                if target is None:
                    raise CrossGameError("target_game_not_found")
                cursor = self.blueprints.find({"studio_id": contract.studio_id}, session=session)
                graph: dict[str, set[str]] = defaultdict(set)
                async for blueprint in cursor:
                    for item in blueprint.get("cross_game_contracts", []):
                        if str(item.get("contract_id")) == contract.contract_id:
                            raise CrossGameError("contract_exists")
                        if item.get("status") == "approved" and item.get("revoked_at") is None:
                            graph[str(item["source_game_id"])].add(str(item["target_game_id"]))
                graph[contract.source_game_id].add(contract.target_game_id)
                if self._has_cycle(graph):
                    raise CrossGameError("cross_game_reward_cycle")
                await self.blueprints.update_one(
                    {"studio_id": contract.studio_id, "game_id": contract.source_game_id},
                    {"$addToSet": {"cross_game_contracts": self._document(contract)}},
                    session=session,
                )

    @staticmethod
    def _has_cycle(graph: Mapping[str, set[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for neighbor in graph.get(node, set()):
                if visit(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)

    async def revoke(self, studio_id: str, source_game_id: str, contract_id: str) -> None:
        now = datetime.now(UTC)
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                result = await self.blueprints.update_one(
                    {
                        "studio_id": studio_id,
                        "game_id": source_game_id,
                        "cross_game_contracts.contract_id": contract_id,
                    },
                    {
                        "$set": {
                            "cross_game_contracts.$.status": "revoked",
                            "cross_game_contracts.$.revoked_at": now,
                        }
                    },
                    session=session,
                )
                if result.modified_count != 1:
                    raise CrossGameError("contract_not_found")
                event_id = new_uuid7()
                await self.outbox.insert_one(
                    {
                        "event_id": event_id,
                        "event_type": "cross_game.contract_revoked.v1",
                        "studio_id": studio_id,
                        "game_id": source_game_id,
                        "contract_id": contract_id,
                        "status": "pending",
                        "occurred_at": now,
                    },
                    session=session,
                )

    async def deliver(
        self,
        contract: CrossGameContract,
        event: SourceEvent,
        target_player_id: str,
        *,
        execute_target: Callable[
            [Any, str, str, str, Mapping[str, Any]], Awaitable[Mapping[str, Any]]
        ],
    ) -> Mapping[str, Any]:
        now = datetime.now(UTC)
        if contract.status != "approved" or (contract.expires_at and contract.expires_at <= now):
            raise CrossGameError("contract_not_approved")
        if (
            event.studio_id != contract.studio_id
            or event.game_id != contract.source_game_id
            or event.event_type not in contract.event_types
            or set(event.payload) - contract.payload_fields
        ):
            raise CrossGameError("source_event_not_authorized")
        for resource, amount in event.payload.items():
            if resource in contract.reward_limits and (
                not isinstance(amount, int)
                or isinstance(amount, bool)
                or amount < 0
                or amount > contract.reward_limits[resource]
            ):
                raise CrossGameError("delivery_reward_limit_exceeded")
        key = {
            "record_type": "cross_game_delivery",
            "contract_id": contract.contract_id,
            "source_event_id": event.event_id,
        }
        try:
            async with await self.client.start_session() as session:
                async with session.start_transaction():
                    stored_source = await self.blueprints.find_one(
                        {
                            "studio_id": contract.studio_id,
                            "game_id": contract.source_game_id,
                            "cross_game_contracts": {
                                "$elemMatch": {
                                    "contract_id": contract.contract_id,
                                    "status": "approved",
                                    "revoked_at": None,
                                }
                            },
                        },
                        session=session,
                    )
                    if stored_source is None:
                        raise CrossGameError("contract_not_approved")
                    prior = await self.receipts.find_one(key, session=session)
                    if prior is not None:
                        if prior.get("quarantined"):
                            raise CrossGameError("delivery_quarantined")
                        return cast(Mapping[str, Any], prior["response"])
                    count = await self.receipts.count_documents(
                        {
                            "record_type": "cross_game_delivery",
                            "contract_id": contract.contract_id,
                            "source_player_id": event.player_id,
                        },
                        session=session,
                    )
                    if count >= contract.max_deliveries_per_player:
                        raise CrossGameError("delivery_limit_exceeded")
                    idempotency_key = f"cross-game:{contract.contract_id}:{event.event_id}"
                    result = await execute_target(
                        session,
                        contract.target_game_id,
                        target_player_id,
                        contract.target_action_id,
                        event.payload,
                    )
                    receipt_id, delivery_id, outbox_id = new_uuid7(), new_uuid7(), new_uuid7()
                    response = {
                        "receipt_id": receipt_id,
                        "delivery_id": delivery_id,
                        "contract_id": contract.contract_id,
                        "source_event_id": event.event_id,
                        "target_action_result": dict(result),
                        "status": "delivered",
                    }
                    await self.receipts.insert_one(
                        {
                            **key,
                            "receipt_id": receipt_id,
                            "delivery_id": delivery_id,
                            "studio_id": contract.studio_id,
                            "source_game_id": contract.source_game_id,
                            "target_game_id": contract.target_game_id,
                            "source_player_id": event.player_id,
                            "target_player_id": target_player_id,
                            "idempotency_key": idempotency_key,
                            "response": response,
                            "status": "delivered",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    await self.outbox.insert_one(
                        {
                            "event_id": outbox_id,
                            "event_type": "cross_game.reward_delivered.v1",
                            "studio_id": contract.studio_id,
                            "game_id": contract.target_game_id,
                            "player_id": target_player_id,
                            "contract_id": contract.contract_id,
                            "source_event_id": event.event_id,
                            "status": "pending",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    return response
        except DuplicateKeyError as error:
            prior = await self.receipts.find_one(key)
            if prior is not None:
                return cast(Mapping[str, Any], prior["response"])
            raise CrossGameError("delivery_conflict") from error
