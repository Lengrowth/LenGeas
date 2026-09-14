from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from packages.domain.authorization.policy import (
    Actor,
    ActorKind,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.identity.merge import MergeService
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, MembershipRole, TrustedScope


class IdentityUnitTests(unittest.TestCase):
    def test_provider_subject_and_device_are_unique(self) -> None:
        repo = InMemoryIdentityRepository()
        first = repo.create_player()
        repo.link_identity(first.player_id, "supabase", "supabase", "sub-1")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "provider_subject_exists"):
            repo.link_identity(repo.create_player().player_id, "supabase", "supabase", "sub-1")  # type: ignore[arg-type]

    def test_merge_collision_requires_choice_and_is_idempotent(self) -> None:
        repo = InMemoryIdentityRepository()
        source, target = repo.create_player(), repo.create_player()
        scope = TrustedScope(
            "actor", "studio", "game", Environment.TESTING, frozenset({MembershipRole.OWNER})
        )
        repo.create_profile(scope, source.player_id, "game")
        repo.create_profile(scope, target.player_id, "game")
        service = MergeService(repo)
        preview = service.preview(scope, source.player_id, target.player_id)
        with self.assertRaisesRegex(ValueError, "merge_selection_required"):
            service.commit(scope, preview.preview_id, {}, "idem-123456")
        result = service.commit(scope, preview.preview_id, {"game": "target"}, "idem-123456")
        self.assertEqual(result, target.player_id)
        self.assertEqual(
            service.commit(scope, preview.preview_id, {"game": "target"}, "idem-123456"),
            target.player_id,
        )

    def test_policy_denies_cross_tenant_and_expired_support(self) -> None:
        service = PolicyDecisionService()
        base = Actor(
            "support",
            ActorKind.ACCOUNT,
            "studio-a",
            frozenset({MembershipRole.SUPPORT}),
            support_case_id="case",
            support_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        expired = service.decide(
            PolicyRequest(base, "read", Resource("player", "p", "studio-a"), Environment.TESTING)
        )
        self.assertEqual(expired.code, "support_grant_expired")
        cross = service.decide(
            PolicyRequest(base, "read", Resource("player", "p", "studio-b"), Environment.TESTING)
        )
        self.assertEqual(cross.code, "tenant_mismatch")
