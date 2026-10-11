"""Identifier generation shared by domain objects."""

from __future__ import annotations

import secrets
import time
from uuid import UUID


def new_uuid7() -> str:
    """Return a lowercase RFC 9562 UUIDv7 string."""
    milliseconds = int(time.time() * 1000) & ((1 << 48) - 1)
    value = (milliseconds << 80) | (0x7 << 76) | (secrets.randbits(12) << 64)
    value |= 0b10 << 62
    value |= secrets.randbits(62)
    return str(UUID(int=value))
