"""Turnstile-bound guest credentials and device-key lifecycle."""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from packages.domain.identity.models import IdentityKind
from packages.domain.identity.repository import InMemoryIdentityRepository


class TurnstileVerifier(Protocol):
    async def verify(self, proof: str, remote_ip: str | None) -> bool: ...


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class GuestCredentials:
    player_id: str
    identity_id: str
    refresh_token: str
    expires_at: datetime


class GuestIdentityService:
    def __init__(
        self,
        repository: InMemoryIdentityRepository,
        turnstile: TurnstileVerifier,
        *,
        max_per_device: int = 3,
    ) -> None:
        self.repository = repository
        self.turnstile = turnstile
        self.max_per_device = max_per_device
        self._used_proofs: set[str] = set()
        self._credential_hashes: dict[str, str] = {}
        self._device_counts: dict[str, int] = {}
        self._device_keys_raw: dict[str, str] = {}

    async def create(
        self, turnstile_proof: str, device_public_key: str, remote_ip: str | None = None
    ) -> GuestCredentials:
        if not turnstile_proof or turnstile_proof in self._used_proofs:
            raise ValueError("turnstile_replay")
        try:
            raw_key = base64.urlsafe_b64decode(
                device_public_key + "=" * (-len(device_public_key) % 4)
            )
            Ed25519PublicKey.from_public_bytes(raw_key)
        except (ValueError, TypeError) as error:
            raise ValueError("invalid_device_key") from error
        if self._device_counts.get(_hash(device_public_key), 0) >= self.max_per_device:
            raise ValueError("guest_abuse_limit")
        if not await self.turnstile.verify(turnstile_proof, remote_ip):
            raise ValueError("turnstile_failed")
        self._used_proofs.add(turnstile_proof)
        player = self.repository.create_player()
        credential = secrets.token_urlsafe(48)
        identity = self.repository.link_identity(
            player.player_id,
            IdentityKind.GUEST,
            "device",
            _hash(credential),
            device_fingerprint=_hash(device_public_key),
        )
        self._credential_hashes[identity.identity_id] = _hash(credential)
        self._device_keys_raw[identity.identity_id] = device_public_key
        device_hash = _hash(device_public_key)
        self._device_counts[device_hash] = self._device_counts.get(device_hash, 0) + 1
        return GuestCredentials(
            player.player_id,
            identity.identity_id,
            credential,
            datetime.now(UTC) + timedelta(days=30),
        )

    def rotate(self, identity_id: str, old_token: str) -> str:
        identity = self.repository.identities.get(identity_id)
        if (
            identity is None
            or identity.revoked_at is not None
            or self._credential_hashes.get(identity_id) != _hash(old_token)
        ):
            raise ValueError("credential_invalid")
        new_token = secrets.token_urlsafe(48)
        self._credential_hashes[identity_id] = _hash(new_token)
        return new_token

    def recover(
        self, identity_id: str, signed_challenge: bytes, challenge: bytes, new_public_key: str
    ) -> str:
        identity = self.repository.identities.get(identity_id)
        if (
            identity is None
            or identity.revoked_at is not None
            or not identity.device_key_fingerprint
        ):
            raise ValueError("credential_invalid")
        old_key = self._device_keys_raw.get(identity_id)
        if old_key is None:
            raise ValueError("device_key_missing")
        try:
            raw_old_key = base64.urlsafe_b64decode(old_key + "=" * (-len(old_key) % 4))
            Ed25519PublicKey.from_public_bytes(raw_old_key).verify(signed_challenge, challenge)
        except Exception as error:
            raise ValueError("device_proof_invalid") from error
        identity.device_key_fingerprint = _hash(new_public_key)
        self._device_keys_raw[identity_id] = new_public_key
        return self.rotate(identity_id, self._credential_hashes[identity_id])
