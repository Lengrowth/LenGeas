from __future__ import annotations

import unittest
from pathlib import Path

from tests.fixture_test_support import digest, load_fixture

SUITE = "determinism"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_determinism_replay.json")


class FixtureDeterminismReplayTests(unittest.TestCase):
    def test_determinism_same_execution_tuple_has_same_digest(self) -> None:
        execution = {
            "seed": FIXTURE["seed"],
            "state": FIXTURE["state"],
            "action_id": "fixture_action",
        }
        self.assertEqual(digest(execution), digest(dict(reversed(list(execution.items())))))

    def test_negative_different_seed_changes_digest(self) -> None:
        original = {"seed": FIXTURE["seed"], "state": FIXTURE["state"]}
        changed = {**original, "seed": "00000000000000000000000000000012"}
        self.assertNotEqual(digest(original), digest(changed))
