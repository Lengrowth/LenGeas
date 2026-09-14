from __future__ import annotations

import unittest

from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, MembershipRole, TrustedScope


class IdentityPropertyTests(unittest.TestCase):
    def test_every_profile_lookup_requires_the_trusted_game_scope(self) -> None:
        repo = InMemoryIdentityRepository()
        player = repo.create_player()
        good = TrustedScope(
            "actor", "studio-a", "game-a", Environment.TESTING, frozenset({MembershipRole.VIEWER})
        )
        repo.create_profile(good, player.player_id, "game-a")
        self.assertEqual(len(repo.profiles_for(good, player.player_id)), 1)
        wrong = TrustedScope(
            "actor", "studio-b", "game-b", Environment.TESTING, frozenset({MembershipRole.VIEWER})
        )
        self.assertEqual(repo.profiles_for(wrong, player.player_id), [])

    def test_state_version_is_never_implicitly_shared_across_profiles(self) -> None:
        repo = InMemoryIdentityRepository()
        player = repo.create_player()
        for game_id in ("game-a", "game-b"):
            scope = TrustedScope(
                "actor",
                "studio-a",
                game_id,
                Environment.TESTING,
                frozenset({MembershipRole.VIEWER}),
            )
            profile = repo.create_profile(scope, player.player_id, game_id)
            profile.state_version += 1
        profiles = repo.profiles_for(
            TrustedScope("actor", "studio-a", None, Environment.TESTING), player.player_id
        )
        self.assertEqual(sorted(p.state_version for p in profiles), [1, 1])
