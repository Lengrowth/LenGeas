"""Guest-to-account merge planning and rollback-safe commit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from packages.domain.audit.events import EventEnvelope
from packages.domain.ids import new_uuid7
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
    studio_id: str
    game_id: str | None


class MergeService:
    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository
        self.previews: dict[str, MergePreview] = {}

    def preview(
        self, scope: TrustedScope, source_player_id: str, target_player_id: str
    ) -> MergePreview:
        if source_player_id == target_player_id:
            raise ValueError("merge_same_player")
        source = self.repository.profiles_for(scope, source_player_id)
        target = self.repository.profiles_for(scope, target_player_id)
        if not source or not target:
            raise PermissionError("player_not_in_studio")
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
            new_uuid7(),
            source_player_id,
            target_player_id,
            collisions,
            entitlements,
            datetime.now(UTC) + timedelta(minutes=10),
            scope.studio_id,
            scope.game_id,
        )
        self.previews[preview.preview_id] = preview
        return preview

    def commit(
        self, scope: TrustedScope, preview_id: str, choices: dict[str, str], idempotency_key: str
    ) -> str:
        preview = self.previews.get(preview_id)
        if preview is None or preview.expires_at < datetime.now(UTC):
            raise ValueError("stale_merge_preview")
        if preview.studio_id != scope.studio_id or preview.game_id != scope.game_id:
            raise PermissionError("merge_scope_mismatch")
        with self.repository.lock:
            prior = self.repository.merge_result(
                scope, preview.source_player_id, preview.target_player_id, idempotency_key
            )
            if prior:
                return prior
            if (
                set(choices) != {collision.game_id for collision in preview.collisions}
                and preview.collisions
            ):
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
                if not self.repository.profiles_for(
                    scope, source.player_id
                ) or not self.repository.profiles_for(scope, target.player_id):
                    raise PermissionError("player_not_in_studio")
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
                self.repository.emit(
                    EventEnvelope.create(
                        "identity.merged.v1",
                        "MergeService",
                        studio_id=scope.studio_id,
                        game_id=scope.game_id,
                        player_id=target.player_id,
                        payload={"source_player_id": preview.source_player_id},
                    )
                )
                self.repository.commit()
                return target.player_id
            except Exception:
                self.repository.rollback()
                raise
