"""MongoDB adapter for studios, memberships, and service accounts."""

from __future__ import annotations

import hashlib
import secrets
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
        await self.database.audit_events.create_index(
            [("studio_id", 1), ("occurred_at", -1)], name="audit_studio_time"
        )
        await self.database.event_outbox.create_index(
            "event_id", unique=True, name="uq_tenancy_event_id"
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
        event = {
            "event_id": new_uuid7(),
            "event_type": "studio.membership_created.v1",
            "studio_id": scope.studio_id,
            "subject_id": membership_id,
            "role": role,
            "occurred_at": datetime.now(UTC),
        }
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                await self.database.studio_memberships.insert_one(
                    {
                        "membership_id": membership_id,
                        "studio_id": scope.studio_id,
                        "account_id": account_id,
                        "role": role,
                        "active": True,
                    },
                    session=session,
                )
                await self.database.audit_events.insert_one(
                    {"action": "studio.membership_created.v1", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)
        return membership_id

    async def change_role(self, scope: TrustedScope, membership_id: str, role: str) -> None:
        event = {
            "event_id": new_uuid7(),
            "event_type": "studio.membership_changed.v1",
            "studio_id": scope.studio_id,
            "subject_id": membership_id,
            "role": role,
            "occurred_at": datetime.now(UTC),
        }
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                result = await self.database.studio_memberships.update_one(
                    {"membership_id": membership_id, "studio_id": scope.studio_id},
                    {"$set": {"role": role}},
                    session=session,
                )
                if result.matched_count != 1:
                    raise KeyError("membership_not_found")
                await self.database.audit_events.insert_one(
                    {"action": "studio.membership_changed.v1", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)

    async def create_service_account(
        self, scope: TrustedScope, name: str, scopes: list[str]
    ) -> dict[str, str]:
        service_account_id = new_uuid7()
        credential = secrets.token_urlsafe(32)
        event = {
            "event_id": new_uuid7(),
            "event_type": "studio.service_account_created.v1",
            "studio_id": scope.studio_id,
            "subject_id": service_account_id,
            "occurred_at": datetime.now(UTC),
        }
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                await self.database.service_accounts.insert_one(
                    {
                        "service_account_id": service_account_id,
                        "studio_id": scope.studio_id,
                        "name": name,
                        "scopes": scopes,
                        "revoked_at": None,
                        "credential_hash": hashlib.sha256(credential.encode()).hexdigest(),
                    },
                    session=session,
                )
                await self.database.audit_events.insert_one(
                    {"action": "studio.service_account_created.v1", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)
        return {"service_account_id": service_account_id, "credential": credential}

    async def revoke_service_account(self, scope: TrustedScope, service_account_id: str) -> None:
        now = datetime.now(UTC)
        event = {
            "event_id": new_uuid7(),
            "event_type": "studio.service_account_revoked.v1",
            "studio_id": scope.studio_id,
            "subject_id": service_account_id,
            "occurred_at": now,
        }
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                result = await self.database.service_accounts.update_one(
                    {
                        "service_account_id": service_account_id,
                        "studio_id": scope.studio_id,
                        "revoked_at": None,
                    },
                    {"$set": {"revoked_at": now}},
                    session=session,
                )
                if result.matched_count == 0:
                    raise KeyError("service_account_not_found")
                await self.database.audit_events.insert_one(
                    {"action": "service_account.revoked", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)

    async def create_invitation(self, scope: TrustedScope, invitation: dict[str, Any]) -> None:
        await self.database.invitations.insert_one({**invitation, "studio_id": scope.studio_id})

    async def verify_service_credential(self, service_account_id: str, credential: str) -> bool:
        value = await self.database.service_accounts.find_one(
            {
                "service_account_id": service_account_id,
                "credential_hash": hashlib.sha256(credential.encode()).hexdigest(),
                "revoked_at": None,
            }
        )
        return value is not None
