"""Guest-to-account merge planning and rollback-safe commit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from packages.domain.tenancy.models import TrustedScope

from .repository import InMemoryIdentityRepository


@dataclass(frozen=True, slots=True)
class MergeCollision:
    game_id: str
    source_profile_id: str
    target_profile_id: str
    choices: tuple[str, ...] = ("source", "target")


@dataclass(frozen=True, slots=True)
class MergePreview:
    preview_id: str
    source_player_id: str
    target_player_id: str
    collisions: tuple[MergeCollision, ...]
    entitlements: tuple[str, ...]
    expires_at: datetime


class MergeService:
    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository
        self.previews: dict[str, MergePreview] = {}

    def preview(
        self, scope: TrustedScope, source_player_id: str, target_player_id: str
    ) -> MergePreview:
        from uuid import uuid4

        source = self.repository.profiles_for(scope, source_player_id)
        target = self.repository.profiles_for(scope, target_player_id)
        target_by_game = {p.game_id: p for p in target}
        collisions = tuple(
            MergeCollision(p.game_id, p.profile_id, target_by_game[p.game_id].profile_id)
            for p in source
            if p.game_id in target_by_game
        )
        entitlements = tuple(
            sorted(
                self.repository.global_profiles[source_player_id].entitlements
                | self.repository.global_profiles[target_player_id].entitlements
            )
        )
        preview = MergePreview(
            uuid4().hex,
            source_player_id,
            target_player_id,
            collisions,
            entitlements,
            datetime.now(UTC) + timedelta(minutes=10),
        )
        self.previews[preview.preview_id] = preview
        return preview

    def commit(
        self, scope: TrustedScope, preview_id: str, choices: dict[str, str], idempotency_key: str
    ) -> str:
        preview = self.previews.get(preview_id)
        if preview is None or preview.expires_at < datetime.now(UTC):
            raise ValueError("stale_merge_preview")
        prior = self.repository.merge_result(
            scope, preview.source_player_id, preview.target_player_id, idempotency_key
        )
        if prior:
            return prior
        if set(choices) != {collision.game_id for collision in preview.collisions}:
            if preview.collisions:
                raise ValueError("merge_selection_required")
        for collision in preview.collisions:
            if choices.get(collision.game_id) not in {"source", "target"}:
                raise ValueError("invalid_merge_selection")
        self.repository.begin()
        try:
            source = self.repository.players[preview.source_player_id]
            target = self.repository.players[preview.target_player_id]
            if source.tombstone or target.tombstone:
                raise ValueError("player_already_merged")
            by_id = {p.profile_id: p for p in self.repository.profiles.values()}
            for collision in preview.collisions:
                if choices[collision.game_id] == "source":
                    by_id[collision.target_profile_id].state = by_id[
                        collision.source_profile_id
                    ].state.copy()
                    by_id[collision.target_profile_id].entitlements = set(
                        by_id[collision.source_profile_id].entitlements
                    )
            self.repository.global_profiles[target.player_id].entitlements.update(
                preview.entitlements
            )
            source.tombstone = True
            for identity in self.repository.all_identities():
                if identity.player_id == source.player_id:
                    identity.revoked_at = datetime.now(UTC)
            self.repository.save_merge_result(scope, idempotency_key, target.player_id)
            self.repository.record_audit(
                scope.actor_id, "identity.merge_committed", scope.studio_id, target.player_id
            )
            self.repository.commit()
            return target.player_id
        except Exception:
            self.repository.rollback()
            raise
