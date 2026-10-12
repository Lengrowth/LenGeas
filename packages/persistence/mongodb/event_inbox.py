"""Mongo consumer inbox uniqueness adapter; handler work shares the session."""

from __future__ import annotations

from typing import Any

from pymongo.errors import DuplicateKeyError


class MongoConsumerInbox:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("consumer", 1), ("event_id", 1)], unique=True)

    async def record_once(self, consumer: str, event_id: str, *, session: Any) -> bool:
        try:
            await self.collection.insert_one(
                {"consumer": consumer, "event_id": event_id}, session=session
            )
        except DuplicateKeyError:
            return False
        return True
