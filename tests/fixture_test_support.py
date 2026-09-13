"""Small, dependency-free helpers shared by synthetic platform fixtures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Return the platform's compact, sorted JSON representation."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return encoded.encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_fixture(directory: Path, filename: str) -> dict[str, Any]:
    path = directory / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("fixture_id", "").startswith("fixture_"):
        raise AssertionError(f"invalid synthetic fixture: {path}")
    return data


def apply_resource_delta(state: Mapping[str, Any], delta: int) -> dict[str, Any]:
    """Apply an integer resource delta without allowing an invalid balance."""
    if isinstance(delta, bool) or not isinstance(delta, int):
        raise TypeError("authoritative resource deltas must be integers")
    balance = state["balance"]
    if not isinstance(balance, int) or isinstance(balance, bool):
        raise TypeError("authoritative balance must be an integer")
    next_balance = balance + delta
    if next_balance < 0:
        raise ValueError("resource balance cannot be negative")
    result = dict(state)
    result["balance"] = next_balance
    return result


def redact(value: Any) -> Any:
    """Recursively redact fields that must not enter logs or telemetry."""
    secret_fields = {"authorization", "password", "secret", "token", "api_key"}
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if key.lower() in secret_fields else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def tenant_read(actor_tenant: str, requested_tenant: str, records: Mapping[str, Any]) -> Any:
    """Model the mandatory tenant filter before a synthetic record lookup."""
    if actor_tenant != requested_tenant:
        raise PermissionError("cross-tenant access denied")
    return records[requested_tenant]
