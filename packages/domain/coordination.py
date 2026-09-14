"""Durable-boundary contracts used by authentication and mutation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RevocationStore(Protocol):
    async def is_jti_revoked(self, jwt_id: str) -> bool: ...

    async def subject_epoch(self, subject: str) -> int: ...

    async def revoke_jti(self, jwt_id: str) -> None: ...

    async def revoke_subject(self, subject: str, epoch: int) -> None: ...


class ProofConsumptionStore(Protocol):
    async def consume(self, proof: str, *, expires_at: float) -> bool: ...


class IdempotencyStore(Protocol):
    async def reserve(
        self,
        *,
        key: str,
        operation: str,
        actor_id: str,
        tenant_id: str | None,
        fingerprint: str,
    ) -> IdempotencyRecord | None: ...

    async def complete(self, key: str, *, status_code: int, body: Any) -> None: ...


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    key: str
    operation: str
    actor_id: str
    tenant_id: str | None
    fingerprint: str
    status_code: int | None = None
    body: Any = None
