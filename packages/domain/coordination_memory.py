"""Process-local coordination stores used only by explicit test composition."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .coordination import IdempotencyRecord


class InMemoryRevocationStore:
    def __init__(self) -> None:
        self.jtis: set[str] = set()
        self.epochs: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def is_jti_revoked(self, jwt_id: str) -> bool:
        async with self._lock:
            return jwt_id in self.jtis

    async def subject_epoch(self, subject: str) -> int:
        async with self._lock:
            return self.epochs.get(subject, -1)

    async def revoke_jti(self, jwt_id: str) -> None:
        async with self._lock:
            self.jtis.add(jwt_id)

    async def revoke_subject(self, subject: str, epoch: int) -> None:
        async with self._lock:
            self.epochs[subject] = max(epoch, self.epochs.get(subject, -1))


class InMemoryProofConsumptionStore:
    def __init__(self) -> None:
        self._proofs: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def consume(self, proof: str, *, expires_at: float) -> bool:
        async with self._lock:
            now = time.monotonic()
            expired = [value for value, deadline in self._proofs.items() if deadline <= now]
            for value in expired:
                self._proofs.pop(value, None)
            if proof in self._proofs:
                return False
            self._proofs[proof] = expires_at
            return True


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    async def reserve(
        self,
        *,
        key: str,
        operation: str,
        actor_id: str,
        tenant_id: str | None,
        fingerprint: str,
    ) -> IdempotencyRecord | None:
        async with self._lock:
            record = self._records.get(key)
            if record is None:
                self._records[key] = IdempotencyRecord(
                    key, operation, actor_id, tenant_id, fingerprint
                )
                return None
            if (
                record.operation != operation
                or record.actor_id != actor_id
                or record.tenant_id != tenant_id
                or record.fingerprint != fingerprint
            ):
                raise ValueError("idempotency_conflict")
            return record

    async def complete(self, key: str, *, status_code: int, body: Any) -> None:
        async with self._lock:
            record = self._records.get(key)
            if record is not None:
                self._records[key] = IdempotencyRecord(
                    record.key,
                    record.operation,
                    record.actor_id,
                    record.tenant_id,
                    record.fingerprint,
                    status_code,
                    body,
                )
