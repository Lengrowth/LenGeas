"""Append-only audit storage with tenant filters and secret scrubbing."""

from __future__ import annotations

from typing import Any

from packages.domain.tenancy.models import TrustedScope


class AuditMongoRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            [("studio_id", 1), ("occurred_at", -1)], name="audit_studio_time"
        )
        await self.collection.create_index(
            [("subject_id", 1), ("occurred_at", -1)], name="audit_subject_time"
        )

    async def append(self, scope: TrustedScope, event: dict[str, Any]) -> None:
        safe = {
            key: value
            for key, value in event.items()
            if key.lower() not in {"token", "authorization", "password", "secret", "api_key"}
        }
        safe["studio_id"] = scope.studio_id
        await self.collection.insert_one(safe)

    async def list_for_scope(self, scope: TrustedScope, subject_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find({"studio_id": scope.studio_id, "subject_id": subject_id})
        return [document async for document in cursor]
