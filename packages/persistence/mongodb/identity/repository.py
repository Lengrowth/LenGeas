"""PyMongo async identity adapter; all queries carry an explicit trusted scope."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

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
