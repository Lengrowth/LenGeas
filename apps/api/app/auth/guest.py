"""Turnstile-bound guest credentials and device-key lifecycle."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from packages.domain.audit.events import EventEnvelope
from packages.domain.coordination import ProofConsumptionStore
from packages.domain.identity.models import IdentityKind
from packages.domain.identity.repository import InMemoryIdentityRepository


class TurnstileVerifier(Protocol):
    async def verify(self, proof: str, remote_ip: str | None) -> bool: ...


class UnconfiguredTurnstile:
    """Production-safe default: no guest is admitted without a provider boundary."""

    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return False


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class GuestCredentials:
    player_id: str
    identity_id: str
    refresh_token: str
    expires_at: datetime


class RepositoryProofConsumptionStore:
    """Repository-bound fallback for provider-independent multi-service tests."""

    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository

    async def consume(self, proof: str, *, expires_at: float) -> bool:
        return self.repository.consume_proof(proof, expires_at)


class GuestIdentityService:
    def __init__(
        self,
        repository: InMemoryIdentityRepository,
        turnstile: TurnstileVerifier,
        *,
        max_per_device: int = 3,
        proof_store: ProofConsumptionStore | None = None,
    ) -> None:
        self.repository = repository
        self.turnstile = turnstile
        self.max_per_device = max_per_device
        self.proof_store = proof_store or RepositoryProofConsumptionStore(repository)
        self._lock = asyncio.Lock()

    async def create(
        self, turnstile_proof: str, device_public_key: str, remote_ip: str | None = None
    ) -> GuestCredentials:
        # The lock makes proof consumption atomic within a process. Production
        # composition must back this boundary with a durable unique proof key.
        async with self._lock:
            return await self._create_unlocked(turnstile_proof, device_public_key, remote_ip)

    async def _create_unlocked(
        self, turnstile_proof: str, device_public_key: str, remote_ip: str | None = None
    ) -> GuestCredentials:
        if not turnstile_proof:
            raise ValueError("turnstile_replay")
        try:
            raw_key = base64.urlsafe_b64decode(
                device_public_key + "=" * (-len(device_public_key) % 4)
            )
            Ed25519PublicKey.from_public_bytes(raw_key)
        except (ValueError, TypeError) as error:
            raise ValueError("invalid_device_key") from error
        device_hash = _hash(device_public_key)
        consumed = await self.proof_store.consume(
            turnstile_proof, expires_at=time.monotonic() + 300
        )
        if not consumed:
            raise ValueError("turnstile_replay")
        if not await self.turnstile.verify(turnstile_proof, remote_ip):
            raise ValueError("turnstile_failed")
        reserve_device = getattr(self.repository, "reserve_guest_device", None)
        if reserve_device is None or not reserve_device(device_hash, self.max_per_device):
            raise ValueError("guest_abuse_limit")
        player = self.repository.create_player()
        credential = secrets.token_urlsafe(48)
        identity = self.repository.link_identity(
            player.player_id,
            IdentityKind.GUEST,
            "device",
            _hash(credential),
            device_fingerprint=_hash(device_public_key),
        )
        save_credential = getattr(self.repository, "save_guest_credential", None)
        if save_credential is None:
            raise RuntimeError("guest_credential_persistence_required")
        save_credential(identity.identity_id, _hash(credential), device_public_key)
        self.repository.emit(
            EventEnvelope.create(
                "identity.guest_created.v1",
                "GuestIdentityService",
                player_id=player.player_id,
                payload={"identity_id": identity.identity_id},
            )
        )
        return GuestCredentials(
            player.player_id,
            identity.identity_id,
            credential,
            datetime.now(UTC) + timedelta(days=30),
        )

    def prove_player(self, player_id: str, credential: str) -> bool:
        for identity in self.repository.identities_for_player(player_id):
            if identity.kind == IdentityKind.GUEST:
                record = self.repository.guest_credential_for(identity.identity_id)
                if record and record.get("credential_hash") == _hash(credential):
                    return True
        return False

    def rotate(self, identity_id: str, old_token: str) -> str:
        lookup_identity = getattr(self.repository, "identity_for_id", None)
        identity = (
            lookup_identity(identity_id)
            if lookup_identity is not None
            else self.repository.identities.get(identity_id)
        )
        record = self.repository.guest_credential_for(identity_id)
        if identity is None or identity.revoked_at is not None or record is None:
            raise ValueError("credential_invalid")
        new_token = secrets.token_urlsafe(48)
        if not self.repository.rotate_guest_credential(
            identity_id, _hash(old_token), _hash(new_token)
        ):
            raise ValueError("credential_invalid")
        return new_token

    def recover(
        self, identity_id: str, signed_challenge: bytes, challenge: bytes, new_public_key: str
    ) -> str:
        lookup_identity = getattr(self.repository, "identity_for_id", None)
        identity = (
            lookup_identity(identity_id)
            if lookup_identity is not None
            else self.repository.identities.get(identity_id)
        )
        if (
            identity is None
            or identity.revoked_at is not None
            or not identity.device_key_fingerprint
        ):
            raise ValueError("credential_invalid")
        record = self.repository.guest_credential_for(identity_id)
        old_key = record.get("device_public_key") if record else None
        if old_key is None:
            raise ValueError("device_key_missing")
        try:
            raw_old_key = base64.urlsafe_b64decode(old_key + "=" * (-len(old_key) % 4))
            Ed25519PublicKey.from_public_bytes(raw_old_key).verify(signed_challenge, challenge)
        except Exception as error:
            raise ValueError("device_proof_invalid") from error
        try:
            raw_new_key = base64.urlsafe_b64decode(
                new_public_key + "=" * (-len(new_public_key) % 4)
            )
            Ed25519PublicKey.from_public_bytes(raw_new_key)
        except (ValueError, TypeError) as error:
            raise ValueError("invalid_device_key") from error
        old_fingerprint = identity.device_key_fingerprint
        new_fingerprint = _hash(new_public_key)
        if old_fingerprint == new_fingerprint:
            raise ValueError("device_key_exists")
        if record is None or "credential_hash" not in record:
            raise ValueError("credential_invalid")
        new_token = secrets.token_urlsafe(48)
        recover = getattr(self.repository, "recover_guest_credential", None)
        if recover is None or not recover(
            identity_id,
            old_fingerprint,
            new_fingerprint,
            _hash(new_token),
            new_public_key,
        ):
            raise ValueError("credential_invalid")
        return new_token
