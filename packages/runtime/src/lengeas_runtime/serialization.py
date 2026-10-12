"""Canonical JSON bytes used for receipt and state digests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        normalized = format(value.normalize(), "f")
        return "0" if normalized in {"-0", "-0.0"} else normalized
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise RuntimeErrorCode("timestamp_must_be_aware")
        return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        raise RuntimeErrorCode("timestamp_invalid")
    if isinstance(value, float):
        raise RuntimeErrorCode("float_forbidden")
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise RuntimeErrorCode("object_key_invalid")
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise RuntimeErrorCode("canonical_value_invalid")


def freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(freeze_value(item) for item in value)
    return value


def thaw_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): thaw_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_value(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(thaw_value(item) for item in value)
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
