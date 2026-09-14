"""PyMongo async identity adapter; all queries carry an explicit trusted scope."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

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
