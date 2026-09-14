"""MongoDB adapter for studios, memberships, and service accounts."""

from __future__ import annotations

from datetime import UTC, datetime
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
            [("studio_id", 1), ("actor_id", 1), ("idempotency_key", 1)],
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

    async def change_role(self, scope: TrustedScope, membership_id: str, role: str) -> None:
        await self.database.studio_memberships.update_one(
            {"membership_id": membership_id, "studio_id": scope.studio_id},
            {"$set": {"role": role}},
        )

    async def create_service_account(
        self, scope: TrustedScope, name: str, scopes: list[str]
    ) -> str:
        service_account_id = new_uuid7()
        await self.database.service_accounts.insert_one(
            {
                "service_account_id": service_account_id,
                "studio_id": scope.studio_id,
                "name": name,
                "scopes": scopes,
                "revoked_at": None,
            }
        )
        return service_account_id

    async def revoke_service_account(self, scope: TrustedScope, service_account_id: str) -> None:
        await self.database.service_accounts.update_one(
            {"service_account_id": service_account_id, "studio_id": scope.studio_id},
            {"$set": {"revoked_at": datetime.now(UTC)}},
        )

    async def create_invitation(self, scope: TrustedScope, invitation: dict[str, Any]) -> None:
        await self.database.invitations.insert_one({**invitation, "studio_id": scope.studio_id})

    async def verify_service_credential(
        self, service_account_id: str, credential_hash: str
    ) -> bool:
        value = await self.database.service_accounts.find_one(
            {
                "service_account_id": service_account_id,
                "credential_hash": credential_hash,
                "revoked_at": None,
            }
        )
        return value is not None
