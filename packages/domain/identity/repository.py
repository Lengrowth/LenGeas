"""Identity repository contract with explicit uniqueness and scope checks."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

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
    return str(uuid4())


class InMemoryIdentityRepository:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.players: dict[str, StudioPlayer] = {}
        self.identities: dict[str, PlayerIdentity] = {}
        self.profiles: dict[str, GameProfile] = {}
        self.global_profiles: dict[str, GlobalProfile] = {}
        self.audit: list[AuditEvent] = []
        self._provider_subject: dict[tuple[str, str], str] = {}
        self._device_keys: dict[str, str] = {}
        self._merge_keys: dict[tuple[str, str], str] = {}
        self._snapshots: list[tuple[Any, ...]] = []

    def create_account(self, email_hash: str | None = None) -> Account:
        account = Account(new_id(), datetime.now(UTC), email_hash)
        self.accounts[account.account_id] = account
        return account

    def create_player(self) -> StudioPlayer:
        player = StudioPlayer(new_id(), datetime.now(UTC))
        self.players[player.player_id] = player
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

    def identity_for_provider(self, provider: str, value: str) -> PlayerIdentity | None:
        identity_id = self._provider_subject.get((provider, value))
        return self.identities.get(identity_id) if identity_id else None

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
            metadata or {},
        )
        self.audit.append(event)
        return event

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
                deepcopy(self._merge_keys),
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
            self._merge_keys,
        ) = snapshot

    def commit(self) -> None:
        if not self._snapshots:
            raise RuntimeError("no_transaction")
        self._snapshots.pop()

    def merge_result(
        self, scope: TrustedScope, source_player: str, target_player: str, idempotency_key: str
    ) -> str | None:
        return self._merge_keys.get((scope.studio_id, idempotency_key))

    def save_merge_result(self, scope: TrustedScope, idempotency_key: str, player_id: str) -> None:
        self._merge_keys[(scope.studio_id, idempotency_key)] = player_id

    def all_identities(self) -> Iterator[PlayerIdentity]:
        return iter(self.identities.values())
