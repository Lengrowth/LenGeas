"""MongoDB persistence for partitioned player-state namespaces."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from packages.domain.ids import new_uuid7
from packages.domain.player_state import (
    MAX_STATE_DOCUMENT_BYTES,
    PlayerStateScope,
    StateDocument,
    StateError,
    StatePatchResponse,
    _canonical_bytes,
    _merge_patch,
    _validate_namespace,
    validate_patch,
)


class MongoPlayerStateRepository:
    """Stores low-frequency profiles separately from bounded namespace state."""

    def __init__(self, database: Any) -> None:
        self.profiles = database.player_profiles
        self.states = database.player_states

    async def ensure_indexes(self) -> None:
        await self.profiles.create_index("profile_id", unique=True, name="uq_player_profile_id")
        await self.profiles.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1)],
            unique=True,
            name="uq_player_profile_scope",
        )
        await self.states.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("namespace_id", 1)],
            unique=True,
            name="uq_player_state_namespace",
        )
        await self.states.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("state_version", 1)],
            name="player_state_scope_version",
        )

    @staticmethod
    def _scope_filter(scope: PlayerStateScope) -> dict[str, str]:
        return {
            "studio_id": scope.studio_id,
            "game_id": scope.game_id,
            "player_id": scope.player_id,
        }

    @classmethod
    def _to_document(cls, raw: dict[str, Any]) -> StateDocument:
        return StateDocument(
            raw["state_id"],
            PlayerStateScope(
                raw["studio_id"], raw["game_id"], raw["player_id"], raw["game_profile_id"]
            ),
            raw["namespace_id"],
            int(raw["state_version"]),
            raw["data"],
            raw["updated_at"],
        )

    async def read(self, scope: PlayerStateScope, namespace_id: str) -> StateDocument | None:
        _validate_namespace(namespace_id)
        raw = await self.states.find_one(
            {**self._scope_filter(scope), "namespace_id": namespace_id}
        )
        return self._to_document(raw) if raw is not None else None

    async def patch(
        self,
        scope: PlayerStateScope,
        namespace_id: str,
        expected_version: int,
        patch: dict[str, Any],
    ) -> StatePatchResponse:
        _validate_namespace(namespace_id)
        validate_patch(patch)
        if expected_version < 0:
            raise StateError("invalid_state_version")
        query = {**self._scope_filter(scope), "namespace_id": namespace_id}
        current = await self.states.find_one(query)
        version = int(current.get("state_version", 0)) if current else 0
        if version != expected_version:
            raise StateError("state_conflict")
        data = _merge_patch(current.get("data", {}) if current else {}, patch)
        encoded = _canonical_bytes(data)
        if len(encoded) > MAX_STATE_DOCUMENT_BYTES:
            raise StateError("state_document_too_large")
        now = datetime.now(UTC)
        state_id = current["state_id"] if current else new_uuid7()
        replacement = {
            **query,
            "state_id": state_id,
            "game_profile_id": scope.game_profile_id,
            "state_version": version + 1,
            "data": data,
            "updated_at": now,
        }
        try:
            if current is None:
                await self.states.insert_one(replacement)
            else:
                result = await self.states.replace_one(
                    {**query, "state_version": expected_version}, replacement
                )
                if result.modified_count != 1:
                    raise StateError("state_conflict")
        except DuplicateKeyError as error:
            raise StateError("state_conflict") from error
        return StatePatchResponse(
            namespace_id,
            version,
            version + 1,
            patch,
            hashlib.sha256(encoded).hexdigest(),
            now,
        )

    async def project(self, scope: PlayerStateScope) -> dict[str, Any]:
        cursor = self.states.find(self._scope_filter(scope)).sort("namespace_id", 1)
        documents = [self._to_document(raw) async for raw in cursor]
        return {
            "player_id": scope.player_id,
            "game_profile_id": scope.game_profile_id,
            "namespace_versions": {
                document.namespace_id: document.state_version for document in documents
            },
            "namespaces": {document.namespace_id: document.data for document in documents},
        }
