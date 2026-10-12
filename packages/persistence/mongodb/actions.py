"""Mongo transaction adapter for player state, receipt, idempotency, and outbox."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from packages.domain.actions import ActionReceipt
from packages.runtime.src.lengeas_runtime.actions import ActionPlan
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.events import OutboxRecord
from packages.runtime.src.lengeas_runtime.serialization import digest, thaw_value


class MongoActionRepository:
    def __init__(self, database: Any) -> None:
        self.states = database.player_states
        self.receipts = database.action_receipts
        self.idempotency = database.idempotency_records
        self.outbox = database.outbox_events
        self.client = database.client

    async def ensure_indexes(self) -> None:
        await self.states.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1)], unique=True
        )
        await self.receipts.create_index("receipt_id", unique=True)
        await self.idempotency.create_index(
            [
                ("studio_id", 1),
                ("game_id", 1),
                ("player_id", 1),
                ("actor_id", 1),
                ("idempotency_key", 1),
            ],
            unique=True,
        )
        await self.outbox.create_index("event_id", unique=True)

    async def commit_action(
        self,
        *,
        studio_id: str,
        game_id: str,
        player_id: str,
        expected_version: int,
        actor_id: str,
        idempotency_key: str,
        fingerprint: str,
        plan: ActionPlan,
        receipt: ActionReceipt,
        outbox: tuple[OutboxRecord, ...],
    ) -> ActionReceipt:
        query = {"studio_id": studio_id, "game_id": game_id, "player_id": player_id}
        idem_query = {**query, "actor_id": actor_id, "idempotency_key": idempotency_key}
        async with await self.client.start_session() as session:
            try:
                async with session.start_transaction():
                    prior = await self.idempotency.find_one(idem_query, session=session)
                    if prior is not None:
                        if prior["fingerprint"] != fingerprint:
                            raise RuntimeErrorCode("idempotency_conflict")
                        return ActionReceipt(**prior["receipt"])
                    state_doc = await self.states.find_one(query, session=session)
                    version = int(state_doc.get("state_version", 0)) if state_doc else 0
                    state = dict(state_doc.get("state", {})) if state_doc else {}
                    if version != expected_version:
                        raise RuntimeErrorCode("state_conflict")
                    from packages.domain.actions import _apply

                    updated_state = _apply(state, plan)
                    updated = ActionReceipt(
                        receipt.receipt_id,
                        receipt.actor_id,
                        receipt.studio_id,
                        receipt.game_id,
                        receipt.player_id,
                        receipt.action_id,
                        receipt.input_digest,
                        receipt.definition_digest,
                        receipt.engine_version,
                        version,
                        version + 1,
                        digest(updated_state),
                        receipt.logical_time,
                        receipt.seed,
                        receipt.status,
                        receipt.explanation,
                        receipt.event_ids,
                    )
                    await self.states.replace_one(
                        query,
                        {**query, "state_version": version + 1, "state": updated_state},
                        upsert=True,
                        session=session,
                    )
                    await self.receipts.insert_one(
                        {
                            "receipt_id": updated.receipt_id,
                            "studio_id": studio_id,
                            "game_id": game_id,
                            "player_id": player_id,
                            "receipt": updated.__dict__
                            if hasattr(updated, "__dict__")
                            else {
                                field: getattr(updated, field)
                                for field in updated.__dataclass_fields__
                            },
                        },
                        session=session,
                    )
                    await self.idempotency.insert_one(
                        {
                            **idem_query,
                            "fingerprint": fingerprint,
                            "receipt": {
                                field: getattr(updated, field)
                                for field in updated.__dataclass_fields__
                            },
                            "created_at": datetime.now(UTC),
                        },
                        session=session,
                    )
                    for record in outbox:
                        await self.outbox.insert_one(
                            {
                                "event_id": record.event_id,
                                "event": thaw_value(
                                    {
                                        field.name: getattr(record.event, field.name)
                                        for field in fields(record.event)
                                    }
                                ),
                                "status": record.status,
                            },
                            session=session,
                        )
                    return updated
            except DuplicateKeyError as error:
                prior = await self.idempotency.find_one(idem_query)
                if prior is not None and prior.get("fingerprint") == fingerprint:
                    return ActionReceipt(**prior["receipt"])
                raise RuntimeErrorCode("idempotency_conflict") from error
