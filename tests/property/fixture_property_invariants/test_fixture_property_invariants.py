from __future__ import annotations

import unittest
from pathlib import Path

from tests.fixture_test_support import apply_resource_delta, load_fixture

SUITE = "property"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_property_invariants.json")


class FixturePropertyInvariantTests(unittest.TestCase):
    def test_positive_conservation_for_balanced_deltas(self) -> None:
        state = {"balance": FIXTURE["initial_balance"]}
        total = 0
        seed = 11
        for _ in range(FIXTURE["seed_count"]):
            seed = (seed * 1_103_515_245 + 12_345) % (2**31)
            delta = (seed % 21) - 10
            if state["balance"] + delta < 0:
                delta = abs(delta)
            state = apply_resource_delta(state, delta)
            total += delta
        self.assertEqual(state["balance"], FIXTURE["initial_balance"] + total)

    def test_negative_property_never_allows_below_zero(self) -> None:
        for balance in range(0, 20):
            with self.subTest(balance=balance):
                with self.assertRaises(ValueError):
                    apply_resource_delta({"balance": balance}, -(balance + 1))
