"""Partitioned, bounded player state with optimistic versioning."""

from __future__ import annotations

import copy
import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from packages.domain.ids import new_uuid7

MAX_STATE_DOCUMENT_BYTES = 6 * 1024 * 1024
MAX_STATE_PATCH_BYTES = 256 * 1024
MAX_NAMESPACE_LENGTH = 64


class StateError(ValueError):
    """A state request violated its scope, version, or resource limit."""


@dataclass(frozen=True, slots=True)
class PlayerStateScope:
    studio_id: str
    game_id: str
    player_id: str
    game_profile_id: str

    def __post_init__(self) -> None:
        if not all((self.studio_id, self.game_id, self.player_id, self.game_profile_id)):
            raise StateError("state_scope_required")


@dataclass(frozen=True, slots=True)
class StateDocument:
    state_id: str
    scope: PlayerStateScope
    namespace_id: str
    state_version: int
    data: Mapping[str, Any]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class StatePatchResponse:
    namespace_id: str
    prior_state_version: int
    state_version: int
    patch: Mapping[str, Any]
    state_digest: str
    updated_at: datetime


class PlayerStateRepository(Protocol):
    async def read(self, scope: PlayerStateScope, namespace_id: str) -> StateDocument | None: ...

    async def patch(
        self,
        scope: PlayerStateScope,
        namespace_id: str,
        expected_version: int,
        patch: Mapping[str, Any],
    ) -> StatePatchResponse: ...

    async def project(self, scope: PlayerStateScope) -> Mapping[str, Any]: ...


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _validate_namespace(namespace_id: str) -> None:
    if not namespace_id or len(namespace_id) > MAX_NAMESPACE_LENGTH:
        raise StateError("invalid_namespace")


def _merge_patch(current: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(current))
    for key, value in patch.items():
        if not isinstance(key, str) or not key or key.startswith("$") or "." in key:
            raise StateError("invalid_state_path")
        if value is None:
            result.pop(key, None)
        elif isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _merge_patch(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_patch(patch: Mapping[str, Any]) -> None:
    try:
        encoded = _canonical_bytes(patch)
    except (TypeError, ValueError) as error:
        raise StateError("state_patch_not_canonical_json") from error
    if len(encoded) > MAX_STATE_PATCH_BYTES:
        raise StateError("state_patch_too_large")


class InMemoryPlayerStateRepository:
    """Thread-safe adapter used for deterministic domain and concurrency tests."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._documents: dict[tuple[str, str, str, str], StateDocument] = {}

    @staticmethod
    def _key(scope: PlayerStateScope, namespace_id: str) -> tuple[str, str, str, str]:
        return (scope.studio_id, scope.game_id, scope.player_id, namespace_id)

    async def read(self, scope: PlayerStateScope, namespace_id: str) -> StateDocument | None:
        _validate_namespace(namespace_id)
        with self._lock:
            document = self._documents.get(self._key(scope, namespace_id))
            return copy.deepcopy(document) if document is not None else None

    async def patch(
        self,
        scope: PlayerStateScope,
        namespace_id: str,
        expected_version: int,
        patch: Mapping[str, Any],
    ) -> StatePatchResponse:
        _validate_namespace(namespace_id)
        validate_patch(patch)
        if expected_version < 0:
            raise StateError("invalid_state_version")
        key = self._key(scope, namespace_id)
        now = datetime.now(UTC)
        with self._lock:
            current = self._documents.get(key)
            current_version = current.state_version if current else 0
            if current_version != expected_version:
                raise StateError("state_conflict")
            current_data = current.data if current else {}
            updated_data = _merge_patch(current_data, patch)
            encoded = _canonical_bytes(updated_data)
            if len(encoded) > MAX_STATE_DOCUMENT_BYTES:
                raise StateError("state_document_too_large")
            import hashlib

            state_id = current.state_id if current else new_uuid7()
            next_version = current_version + 1
            document = StateDocument(state_id, scope, namespace_id, next_version, updated_data, now)
            self._documents[key] = document
            return StatePatchResponse(
                namespace_id,
                current_version,
                next_version,
                copy.deepcopy(dict(patch)),
                hashlib.sha256(encoded).hexdigest(),
                now,
            )

    async def project(self, scope: PlayerStateScope) -> Mapping[str, Any]:
        with self._lock:
            documents = {
                key[3]: copy.deepcopy(document)
                for key, document in self._documents.items()
                if key[:3] == (scope.studio_id, scope.game_id, scope.player_id)
            }
        return {
            "player_id": scope.player_id,
            "game_profile_id": scope.game_profile_id,
            "namespace_versions": {
                namespace: document.state_version
                for namespace, document in sorted(documents.items())
            },
            "namespaces": {namespace: document.data for namespace, document in documents.items()},
        }
