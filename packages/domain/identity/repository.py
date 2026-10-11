"""Identity repository contract with explicit uniqueness and scope checks."""

from __future__ import annotations

import time
from collections.abc import Iterator
from copy import deepcopy
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from packages.domain.audit.events import EventEnvelope, _scrub
from packages.domain.ids import new_uuid7
from packages.domain.tenancy.models import TrustedScope

from .models import (
    Account,
    AuditEvent,
    GameProfile,
    GlobalProfile,
    IdentityKind,
    PlayerIdentity,
    StudioPlayer,
)


def new_id() -> str:
    return new_uuid7()


class InMemoryIdentityRepository:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.players: dict[str, StudioPlayer] = {}
        self.identities: dict[str, PlayerIdentity] = {}
        self.profiles: dict[str, GameProfile] = {}
        self.global_profiles: dict[str, GlobalProfile] = {}
        self.audit: list[AuditEvent] = []
        self.events: list[EventEnvelope] = []
        self.outbox: list[EventEnvelope] = []
        self.privacy_requests: dict[str, Any] = {}
        self.privacy_holds: set[str] = set()
        self.financial_history: dict[str, dict[str, str]] = {}
        self.player_studios: dict[str, set[str]] = {}
        self._provider_subject: dict[tuple[str, str], str] = {}
        self._device_keys: dict[str, str] = {}
        self._proof_consumed: dict[str, float] = {}
        self.guest_credentials: dict[str, dict[str, str]] = {}
        self.guest_device_counts: dict[str, int] = {}
        self._merge_keys: dict[tuple[str, str, str], str] = {}
        self._merge_fingerprints: dict[tuple[str, str, str], str] = {}
        self.merge_previews: dict[str, Any] = {}
        self._snapshots: list[tuple[Any, ...]] = []
        self.lock = RLock()

    def create_account(self, email_hash: str | None = None) -> Account:
        account = Account(new_id(), datetime.now(UTC), email_hash)
        self.accounts[account.account_id] = account
        return account

    def create_player(self) -> StudioPlayer:
        player = StudioPlayer(new_id(), datetime.now(UTC))
        self.players[player.player_id] = player
        self.player_studios[player.player_id] = set()
        self.global_profiles[player.player_id] = GlobalProfile(player.player_id)
        return player

    def link_identity(
        self,
        player_id: str,
        kind: IdentityKind,
        provider: str,
        value: str,
        *,
        device_fingerprint: str | None = None,
        account_id: str | None = None,
    ) -> PlayerIdentity:
        if player_id not in self.players:
            raise KeyError("player_not_found")
        key = (provider, value)
        existing = self._provider_subject.get(key)
        if existing is not None:
            raise ValueError("provider_subject_exists")
        if device_fingerprint and device_fingerprint in self._device_keys:
            raise ValueError("device_key_exists")
        identity = PlayerIdentity(
            new_id(),
            player_id,
            kind,
            provider,
            value,
            datetime.now(UTC),
            device_key_fingerprint=device_fingerprint,
            account_id=account_id,
        )
        self.identities[identity.identity_id] = identity
        self._provider_subject[key] = identity.identity_id
        if device_fingerprint:
            self._device_keys[device_fingerprint] = identity.identity_id
        return identity

    def replace_device_key(
        self, identity_id: str, old_fingerprint: str, new_fingerprint: str
    ) -> None:
        identity = self.identities.get(identity_id)
        if identity is None or identity.device_key_fingerprint != old_fingerprint:
            raise ValueError("device_key_mismatch")
        owner = self._device_keys.get(new_fingerprint)
        if owner is not None and owner != identity_id:
            raise ValueError("device_key_exists")
        self._device_keys.pop(old_fingerprint, None)
        self._device_keys[new_fingerprint] = identity_id
        identity.device_key_fingerprint = new_fingerprint

    def reserve_guest_device(self, device_hash: str, maximum: int) -> bool:
        """Atomically reserve one guest slot for a device in this repository."""
        with self.lock:
            count = self.guest_device_counts.get(device_hash, 0)
            if count >= maximum:
                return False
            self.guest_device_counts[device_hash] = count + 1
            return True

    def consume_proof(self, proof: str, expires_at: float) -> bool:
        with self.lock:
            now = time.monotonic()
            self._proof_consumed = {
                key: expiry for key, expiry in self._proof_consumed.items() if expiry > now
            }
            if proof in self._proof_consumed:
                return False
            self._proof_consumed[proof] = expires_at
            return True

    def save_guest_credential(
        self, identity_id: str, credential_hash: str, device_public_key: str
    ) -> None:
        self.guest_credentials[identity_id] = {
            "credential_hash": credential_hash,
            "device_public_key": device_public_key,
        }

    def guest_credential_for(self, identity_id: str) -> dict[str, str] | None:
        return self.guest_credentials.get(identity_id)

    def rotate_guest_credential(self, identity_id: str, old_hash: str, new_hash: str) -> bool:
        record = self.guest_credentials.get(identity_id)
        if record is None or record.get("credential_hash") != old_hash:
            return False
        record["credential_hash"] = new_hash
        return True

    def recover_guest_credential(
        self,
        identity_id: str,
        old_fingerprint: str,
        new_fingerprint: str,
        new_hash: str,
        new_public_key: str,
    ) -> bool:
        identity = self.identities.get(identity_id)
        if identity is None or identity.device_key_fingerprint != old_fingerprint:
            return False
        self.replace_device_key(identity_id, old_fingerprint, new_fingerprint)
        self.save_guest_credential(identity_id, new_hash, new_public_key)
        return True

    def identity_for_provider(self, provider: str, value: str) -> PlayerIdentity | None:
        identity_id = self._provider_subject.get((provider, value))
        return self.identities.get(identity_id) if identity_id else None

    def identity_for_id(self, identity_id: str) -> PlayerIdentity | None:
        return self.identities.get(identity_id)

    def account_for_player(self, player_id: str) -> Account | None:
        return next(
            (account for account in self.accounts.values() if account.player_id == player_id),
            None,
        )

    def identities_for_player(self, player_id: str) -> list[PlayerIdentity]:
        return [
            identity for identity in self.identities.values() if identity.player_id == player_id
        ]

    def create_profile(self, scope: TrustedScope, player_id: str, game_id: str) -> GameProfile:
        if scope.game_id != game_id:
            raise PermissionError("game_scope_mismatch")
        if player_id not in self.players or self.players[player_id].tombstone:
            raise KeyError("player_not_found")
        if any(
            p.player_id == player_id and p.game_id == game_id and p.studio_id == scope.studio_id
            for p in self.profiles.values()
        ):
            raise ValueError("game_profile_exists")
        profile = GameProfile(new_id(), player_id, scope.studio_id, game_id)
        self.profiles[profile.profile_id] = profile
        self.player_studios.setdefault(player_id, set()).add(scope.studio_id)
        return profile

    def profiles_for(self, scope: TrustedScope, player_id: str) -> list[GameProfile]:
        return [
            p
            for p in self.profiles.values()
            if p.studio_id == scope.studio_id
            and p.player_id == player_id
            and (scope.game_id is None or p.game_id == scope.game_id)
        ]

    def record_audit(
        self,
        actor_id: str,
        action: str,
        studio_id: str | None,
        subject_id: str | None,
        metadata: dict[str, str] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            new_id(),
            actor_id,
            action,
            studio_id,
            subject_id,
            datetime.now(UTC),
            _scrub(metadata or {}),
        )
        self.audit.append(event)
        return event

    def emit(self, event: EventEnvelope) -> None:
        self.events.append(event)
        self.outbox.append(event)

    def begin(self) -> None:
        self._snapshots.append(
            (
                deepcopy(self.accounts),
                deepcopy(self.players),
                deepcopy(self.identities),
                deepcopy(self.profiles),
                deepcopy(self.global_profiles),
                deepcopy(self._provider_subject),
                deepcopy(self._device_keys),
                deepcopy(self._proof_consumed),
                deepcopy(self.guest_credentials),
                deepcopy(self.guest_device_counts),
                deepcopy(self._merge_keys),
                deepcopy(self._merge_fingerprints),
                deepcopy(self.merge_previews),
                deepcopy(self.audit),
                deepcopy(self.events),
                deepcopy(self.outbox),
                deepcopy(self.player_studios),
                deepcopy(self.privacy_requests),
                deepcopy(self.privacy_holds),
                deepcopy(self.financial_history),
            )
        )

    def rollback(self) -> None:
        if not self._snapshots:
            raise RuntimeError("no_transaction")
        snapshot = self._snapshots.pop()
        (
            self.accounts,
            self.players,
            self.identities,
            self.profiles,
            self.global_profiles,
            self._provider_subject,
            self._device_keys,
            self._proof_consumed,
            self.guest_credentials,
            self.guest_device_counts,
            self._merge_keys,
            self._merge_fingerprints,
            self.merge_previews,
            self.audit,
            self.events,
            self.outbox,
            self.player_studios,
            self.privacy_requests,
            self.privacy_holds,
            self.financial_history,
        ) = snapshot

    def commit(self) -> None:
        if not self._snapshots:
            raise RuntimeError("no_transaction")
        self._snapshots.pop()

    def merge_result(
        self,
        scope: TrustedScope,
        source_player: str,
        target_player: str,
        idempotency_key: str,
        fingerprint: str | None = None,
    ) -> str | None:
        result = self._merge_keys.get((scope.studio_id, scope.actor_id, idempotency_key))
        if result is not None and fingerprint is not None:
            stored = getattr(self, "_merge_fingerprints", {}).get(
                (scope.studio_id, scope.actor_id, idempotency_key)
            )
            if stored != fingerprint:
                raise ValueError("idempotency_conflict")
        return result

    def save_merge_result(
        self,
        scope: TrustedScope,
        idempotency_key: str,
        player_id: str,
        fingerprint: str | None = None,
    ) -> None:
        key = (scope.studio_id, scope.actor_id, idempotency_key)
        self._merge_keys[key] = player_id
        if fingerprint is not None:
            self._merge_fingerprints[key] = fingerprint

    def save_merge_preview(self, preview: Any) -> None:
        self.merge_previews[preview.preview_id] = preview

    def merge_preview_for(self, preview_id: str) -> Any | None:
        return self.merge_previews.get(preview_id)

    def set_legal_hold(self, account_id: str) -> None:
        self.privacy_holds.add(account_id)

    def has_legal_hold(self, account_id: str) -> bool:
        return account_id in self.privacy_holds

    def all_identities(self) -> Iterator[PlayerIdentity]:
        return iter(self.identities.values())
