"""PyMongo async identity adapter; all queries carry an explicit trusted scope."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

from pymongo.errors import DuplicateKeyError

from packages.domain.ids import new_uuid7
from packages.domain.tenancy.models import TrustedScope


class IdentityMongoRepository:
    COLLECTIONS = (
        "accounts",
        "studio_players",
        "player_identities",
        "game_profiles",
        "global_profiles",
    )

    def __init__(self, database: Any) -> None:
        self.database = database

    async def ensure_indexes(self) -> None:
        await self.database.accounts.create_index("account_id", unique=True)
        await self.database.player_identities.create_index(
            [("provider", 1), ("subject_or_credential_hash", 1)],
            unique=True,
            name="uq_provider_subject",
        )
        await self.database.player_identities.create_index(
            "device_key_fingerprint", unique=True, sparse=True, name="uq_guest_device_key"
        )
        await self.database.game_profiles.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1)],
            unique=True,
            name="uq_game_profile",
        )
        await self.database.merge_previews.create_index(
            "preview_id", unique=True, name="uq_merge_preview_id"
        )
        await self.database.merge_previews.create_index(
            "expires_at", expireAfterSeconds=0, name="merge_preview_expiry"
        )
        await self.database.guest_credentials.create_index(
            "identity_id", unique=True, name="uq_guest_credential_identity"
        )
        await self.database.guest_device_counts.create_index(
            "device_hash", unique=True, name="uq_guest_device_hash"
        )
        await self.database.privacy_requests.create_index(
            "request_id", unique=True, name="uq_privacy_request"
        )
        await self.database.financial_history.create_index(
            [("studio_id", 1), ("account_id", 1)], unique=True, name="uq_financial_history_scope"
        )
        await self.database.audit_events.create_index(
            [("studio_id", 1), ("occurred_at", -1)], name="audit_studio_time"
        )
        await self.database.event_outbox.create_index("event_id", unique=True, name="uq_event_id")

    async def save_merge_preview(self, preview: Mapping[str, Any]) -> None:
        await self.database.merge_previews.replace_one(
            {"preview_id": preview["preview_id"]}, dict(preview), upsert=True
        )

    async def find_merge_preview(
        self, scope: TrustedScope, preview_id: str
    ) -> Mapping[str, Any] | None:
        return cast(
            Mapping[str, Any] | None,
            await self.database.merge_previews.find_one(
                {"preview_id": preview_id, "studio_id": scope.studio_id}
            ),
        )

    @staticmethod
    def _filter(scope: TrustedScope, **extra: Any) -> dict[str, Any]:
        result: dict[str, Any] = {"studio_id": scope.studio_id}
        if scope.game_id is not None:
            result["game_id"] = scope.game_id
        result.update(extra)
        return result

    async def find_profile(self, scope: TrustedScope, player_id: str) -> Mapping[str, Any] | None:
        value = await self.database.game_profiles.find_one(self._filter(scope, player_id=player_id))
        return cast(Mapping[str, Any] | None, value)

    async def create_account(self, email_hash: str | None = None) -> str:
        account_id = new_uuid7()
        await self.database.accounts.insert_one(
            {"account_id": account_id, "email_hash": email_hash}
        )
        return account_id

    async def create_player(self) -> str:
        player_id = new_uuid7()
        await self.database.studio_players.insert_one({"player_id": player_id, "tombstone": False})
        await self.database.global_profiles.insert_one({"player_id": player_id, "entitlements": []})
        return player_id

    async def find_identity(self, provider: str, subject: str) -> Mapping[str, Any] | None:
        return cast(
            Mapping[str, Any] | None,
            await self.database.player_identities.find_one(
                {
                    "provider": provider,
                    "subject_or_credential_hash": subject,
                    "revoked_at": {"$exists": False},
                }
            ),
        )

    async def create_profile(
        self,
        scope: TrustedScope,
        player_id: str,
        game_id: str,
        state: Mapping[str, Any] | None = None,
    ) -> str:
        if scope.game_id != game_id:
            raise PermissionError("game_scope_mismatch")
        profile_id = new_uuid7()
        await self.database.game_profiles.insert_one(
            {
                "profile_id": profile_id,
                "player_id": player_id,
                "studio_id": scope.studio_id,
                "game_id": game_id,
                "state": dict(state or {}),
                "state_version": 0,
            }
        )
        return profile_id

    async def list_profiles(self, scope: TrustedScope, player_id: str) -> list[Mapping[str, Any]]:
        cursor = self.database.game_profiles.find(self._filter(scope, player_id=player_id))
        return [document async for document in cursor]

    async def link_identity(
        self,
        scope: TrustedScope,
        player_id: str,
        provider: str,
        subject: str,
        account_id: str | None = None,
    ) -> str:
        identity_id = new_uuid7()
        await self.database.player_identities.insert_one(
            {
                "identity_id": identity_id,
                "player_id": player_id,
                "provider": provider,
                "subject_or_credential_hash": subject,
                "account_id": account_id,
            }
        )
        return identity_id

    async def record_audit(self, scope: TrustedScope, event: Mapping[str, Any]) -> None:
        await self.database.audit_events.insert_one({**dict(event), "studio_id": scope.studio_id})

    async def append_event(self, event: Mapping[str, Any]) -> None:
        await self.database.event_outbox.insert_one(dict(event))

    async def create_privacy_request(self, request: Mapping[str, Any]) -> None:
        document = dict(request)
        document.setdefault("status", "queued")
        await self.database.privacy_requests.insert_one(document)

    async def complete_privacy_request(
        self, scope: TrustedScope, request_id: str, status: str, event: Mapping[str, Any]
    ) -> None:
        await self.database.privacy_requests.update_one(
            {"request_id": request_id, "studio_id": scope.studio_id},
            {"$set": {"status": status, "completed_at": datetime.now(UTC)}},
        )
        await self.record_audit(scope, {**dict(event), "action": "privacy.completed"})
        await self.append_event(
            {
                **dict(event),
                "event_id": new_uuid7(),
                "event_type": "privacy.completed.v1",
                "studio_id": scope.studio_id,
                "occurred_at": datetime.now(UTC),
            }
        )

    async def delete_account(
        self,
        scope: TrustedScope,
        account_id: str,
        pseudonym: str,
        request_id: str,
    ) -> None:
        now = datetime.now(UTC)
        account_filter = {"account_id": account_id}
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                await self.database.accounts.update_one(
                    account_filter,
                    {
                        "$set": {
                            "deleted_at": now,
                            "email_hash": None,
                            "tombstone": True,
                            "pseudonym": pseudonym,
                        },
                        "$inc": {"session_epoch": 1},
                    },
                    session=session,
                )
                identities = self.database.player_identities.find(
                    {"account_id": account_id}, session=session
                )
                player_ids = [document["player_id"] async for document in identities]
                await self.database.player_identities.update_many(
                    {"account_id": account_id}, {"$set": {"revoked_at": now}}, session=session
                )
                if player_ids:
                    await self.database.studio_players.update_many(
                        {"player_id": {"$in": player_ids}},
                        {"$set": {"tombstone": True, "deleted_at": now}},
                        session=session,
                    )
                await self.database.financial_history.update_one(
                    {"studio_id": scope.studio_id, "account_id": account_id},
                    {
                        "$set": {
                            "studio_id": scope.studio_id,
                            "account_id": account_id,
                            "pseudonym": pseudonym,
                            "request_id": request_id,
                            "updated_at": now,
                        }
                    },
                    upsert=True,
                    session=session,
                )
                event = {
                    "event_id": new_uuid7(),
                    "event_type": "privacy.deleted.v1",
                    "studio_id": scope.studio_id,
                    "subject_id": account_id,
                    "request_id": request_id,
                    "occurred_at": now,
                }
                await self.database.audit_events.insert_one(
                    {"action": "privacy.deleted", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)

    async def merge_players(
        self,
        scope: TrustedScope,
        source_player_id: str,
        target_player_id: str,
        idempotency_key: str,
        payload_digest: str,
    ) -> None:
        existing = await self.database.merge_idempotency.find_one(
            {
                "studio_id": scope.studio_id,
                "actor_id": scope.actor_id,
                "idempotency_key": idempotency_key,
            }
        )
        if existing is not None:
            if existing.get("payload_digest") != payload_digest:
                raise ValueError("idempotency_conflict")
            return
        event = {
            "event_id": new_uuid7(),
            "event_type": "identity.merged.v1",
            "studio_id": scope.studio_id,
            "player_id": target_player_id,
            "source_player_id": source_player_id,
            "occurred_at": datetime.now(UTC),
        }
        async with self.database.client.start_session() as session:
            async with session.start_transaction():
                try:
                    await self.database.merge_idempotency.insert_one(
                        {
                            "studio_id": scope.studio_id,
                            "actor_id": scope.actor_id,
                            "idempotency_key": idempotency_key,
                            "payload_digest": payload_digest,
                            "source_player_id": source_player_id,
                            "target_player_id": target_player_id,
                        },
                        session=session,
                    )
                except DuplicateKeyError as error:
                    replay = await self.database.merge_idempotency.find_one(
                        {
                            "studio_id": scope.studio_id,
                            "actor_id": scope.actor_id,
                            "idempotency_key": idempotency_key,
                        },
                        session=session,
                    )
                    if replay is None or replay.get("payload_digest") != payload_digest:
                        raise ValueError("idempotency_conflict") from error
                    return
                await self.database.studio_players.update_one(
                    {"player_id": source_player_id},
                    {"$set": {"tombstone": True}},
                    session=session,
                )
                await self.database.player_identities.update_many(
                    {"player_id": source_player_id},
                    {"$set": {"revoked_at": datetime.now(UTC)}},
                    session=session,
                )
                await self.database.audit_events.insert_one(
                    {"action": "identity.merge_committed", **event}, session=session
                )
                await self.database.event_outbox.insert_one(event, session=session)
