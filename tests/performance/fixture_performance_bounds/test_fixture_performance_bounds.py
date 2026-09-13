from __future__ import annotations

import time
import unittest
from pathlib import Path

from tests.fixture_test_support import canonical_json, load_fixture

SUITE = "performance"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_performance_bounds.json")


class FixturePerformanceBoundTests(unittest.TestCase):
    def test_bounded_performance_canonicalizes_small_state(self) -> None:
        state = {
            "balance": 7,
            "state_version": 2,
            "studio_id": "fixture_studio",
            "tags": ["a", "b"],
        }
        started = time.perf_counter()
        for _ in range(FIXTURE["iterations"]):
            canonical_json(state)
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, FIXTURE["max_seconds"])

    def test_negative_performance_budget_is_not_accepted(self) -> None:
        self.assertGreater(FIXTURE["max_seconds"], 0)
