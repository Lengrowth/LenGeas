"""Typed state-path registry; evaluator never accepts arbitrary JSONPath."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode


class MissingRule(StrEnum):
    ERROR = "error"
    ALLOW_ABSENCE = "allow_absence"


@dataclass(frozen=True, slots=True)
class StatePath:
    token: str
    namespace: str
    owner_package: str
    value_type: type | tuple[type, ...]
    readable_by: frozenset[str]
    writable_by: frozenset[str]
    missing_rule: MissingRule = MissingRule.ERROR


class StatePathRegistry:
    def __init__(self) -> None:
        self._paths: dict[str, StatePath] = {}
        self._frozen = False

    def register(self, path: StatePath) -> None:
        if self._frozen:
            raise RuntimeErrorCode("registry_frozen")
        if path.token in self._paths:
            raise RuntimeErrorCode("state_path_duplicate")
        if not path.token or not path.namespace or not path.owner_package:
            raise RuntimeErrorCode("state_path_invalid")
        parts = path.token.split(".")
        if (
            parts[0] != path.namespace
            or len(parts) < 2
            or any(not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", part) for part in parts)
            or path.owner_package not in path.writable_by
        ):
            raise RuntimeErrorCode("state_path_invalid")
        self._paths[path.token] = path

    def freeze(self) -> None:
        self._frozen = True

    def resolve(self, token: str, package_id: str, *, write: bool = False) -> StatePath:
        path = self._paths.get(token)
        if path is None:
            raise RuntimeErrorCode("state_path_unregistered")
        permissions = path.writable_by if write else path.readable_by
        if package_id not in permissions:
            raise RuntimeErrorCode("state_path_write_denied" if write else "state_path_read_denied")
        if write and package_id != path.owner_package:
            raise RuntimeErrorCode("namespace_owner_mismatch")
        return path

    def read(self, state: Mapping[str, Any], token: str, package_id: str) -> Any:
        path = self.resolve(token, package_id)
        namespace_value = state.get(path.namespace)
        cursor: Any = namespace_value
        for part in token.split(".")[1:]:
            if not isinstance(cursor, Mapping) or part not in cursor:
                if path.missing_rule == MissingRule.ALLOW_ABSENCE:
                    return _MISSING
                raise RuntimeErrorCode("state_path_missing")
            cursor = cursor[part]
        if cursor is _MISSING:
            return cursor
        integer_type = path.value_type is int or (
            isinstance(path.value_type, tuple) and int in path.value_type
        )
        if not isinstance(cursor, path.value_type) or isinstance(cursor, bool) and integer_type:
            raise RuntimeErrorCode("state_path_type_mismatch")
        return cursor


class _Missing:
    pass


_MISSING = _Missing()


def is_missing(value: object) -> bool:
    return value is _MISSING


def path_token(value: Any) -> str:
    """Translate a schema StatePath object into its stable registry token."""
    if isinstance(value, str):
        return value
    if not isinstance(value, Mapping):
        raise RuntimeErrorCode("state_path_invalid")
    namespace = value.get("namespace_id")
    segments = value.get("segments")
    if not isinstance(namespace, str) or not isinstance(segments, (list, tuple)):
        raise RuntimeErrorCode("state_path_invalid")
    if not segments or any(not isinstance(segment, str) for segment in segments):
        raise RuntimeErrorCode("state_path_invalid")
    return ".".join((namespace, *segments))
