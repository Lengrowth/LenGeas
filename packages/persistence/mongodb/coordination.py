"""Atomic MongoDB coordination primitives for cross-worker security state."""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from packages.domain.coordination import IdempotencyRecord


class MongoCoordinationStore:
    def __init__(self, database: Any) -> None:
        self.database = database

    async def ensure_indexes(self) -> None:
        await self.database.jwt_revocations.create_index(
            "jwt_id", unique=True, sparse=True, name="uq_revoked_jti"
        )
        await self.database.jwt_revocations.create_index(
            "subject", unique=True, sparse=True, name="uq_revoked_subject"
        )
        await self.database.proof_consumptions.create_index(
            "proof_hash", unique=True, name="uq_consumed_proof"
        )
        await self.database.proof_consumptions.create_index(
            "expires_at", expireAfterSeconds=0, name="proof_consumption_expiry"
        )
        await self.database.idempotency.create_index("key", unique=True, name="uq_idempotency_key")

    async def is_jti_revoked(self, jwt_id: str) -> bool:
        return await self.database.jwt_revocations.find_one({"jwt_id": jwt_id}) is not None

    async def subject_epoch(self, subject: str) -> int:
        document = await self.database.jwt_revocations.find_one({"subject": subject})
        return int(document.get("epoch", -1)) if document else -1

    async def revoke_jti(self, jwt_id: str) -> None:
        await self.database.jwt_revocations.update_one(
            {"jwt_id": jwt_id}, {"$set": {"jwt_id": jwt_id, "revoked_at": time.time()}}, upsert=True
        )

    async def revoke_subject(self, subject: str, epoch: int) -> None:
        await self.database.jwt_revocations.update_one(
            {"subject": subject},
            {
                "$set": {"subject": subject, "revoked_at": time.time()},
                "$max": {"epoch": epoch},
            },
            upsert=True,
        )

    async def consume(self, proof: str, *, expires_at: float) -> bool:
        try:
            await self.database.proof_consumptions.insert_one(
                {
                    "proof_hash": hashlib.sha256(proof.encode()).hexdigest(),
                    "consumed_at": time.time(),
                    "expires_at": datetime.fromtimestamp(expires_at, UTC),
                }
            )
        except DuplicateKeyError:
            return False
        return True

    async def reserve(
        self,
        *,
        key: str,
        operation: str,
        actor_id: str,
        tenant_id: str | None,
        fingerprint: str,
    ) -> IdempotencyRecord | None:
        try:
            await self.database.idempotency.insert_one(
                {
                    "key": key,
                    "operation": operation,
                    "actor_id": actor_id,
                    "tenant_id": tenant_id,
                    "fingerprint": fingerprint,
                    "status_code": None,
                    "body": None,
                }
            )
            return None
        except DuplicateKeyError as error:
            document = await self.database.idempotency.find_one({"key": key})
            if document is None:
                raise RuntimeError("idempotency_record_lost") from error
            if any(
                document.get(field) != value
                for field, value in {
                    "operation": operation,
                    "actor_id": actor_id,
                    "tenant_id": tenant_id,
                    "fingerprint": fingerprint,
                }.items()
            ):
                raise ValueError("idempotency_conflict") from error
            return IdempotencyRecord(
                key,
                operation,
                actor_id,
                tenant_id,
                fingerprint,
                document.get("status_code"),
                document.get("body"),
            )

    async def complete(self, key: str, *, status_code: int, body: Any) -> None:
        await self.database.idempotency.update_one(
            {"key": key}, {"$set": {"status_code": status_code, "body": body}}
        )
