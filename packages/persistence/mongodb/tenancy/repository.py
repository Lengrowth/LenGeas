"""MongoDB adapter for studios, memberships, and service accounts."""

from __future__ import annotations

from typing import Any, cast

from packages.domain.ids import new_uuid7
from packages.domain.tenancy.models import TrustedScope


class TenancyMongoRepository:
    def __init__(self, database: Any) -> None:
        self.database = database

    async def ensure_indexes(self) -> None:
        await self.database.studio_memberships.create_index(
            [("studio_id", 1), ("account_id", 1)], unique=True, name="uq_studio_membership"
        )
        await self.database.service_accounts.create_index(
            "client_id", unique=True, name="uq_service_client_id"
        )
        await self.database.studios.create_index("slug", unique=True, name="uq_studio_slug")
        await self.database.merge_idempotency.create_index(
            [("studio_id", 1), ("idempotency_key", 1)],
            unique=True,
            name="uq_merge_idempotency_scope",
        )

    async def list_memberships(self, scope: TrustedScope) -> list[dict[str, Any]]:
        cursor = self.database.studio_memberships.find({"studio_id": scope.studio_id})
        return [document async for document in cursor]

    async def membership_for(self, studio_id: str, account_id: str) -> dict[str, Any] | None:
        value = await self.database.studio_memberships.find_one(
            {"studio_id": studio_id, "account_id": account_id, "active": True}
        )
        return cast(dict[str, Any] | None, value)

    async def create_studio(self, scope: TrustedScope, name: str, slug: str) -> str:
        studio_id = new_uuid7()
        await self.database.studios.insert_one({"studio_id": studio_id, "name": name, "slug": slug})
        return studio_id

    async def create_membership(self, scope: TrustedScope, account_id: str, role: str) -> str:
        membership_id = new_uuid7()
        await self.database.studio_memberships.insert_one(
            {
                "membership_id": membership_id,
                "studio_id": scope.studio_id,
                "account_id": account_id,
                "role": role,
                "active": True,
            }
        )
        return membership_id
