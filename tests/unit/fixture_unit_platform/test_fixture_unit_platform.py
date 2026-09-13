from __future__ import annotations

import unittest
from pathlib import Path

from tests.fixture_test_support import apply_resource_delta, load_fixture

SUITE = "unit"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_unit_platform.json")


class FixtureUnitPlatformTests(unittest.TestCase):
    def test_positive_integer_delta_updates_state(self) -> None:
        self.assertEqual(apply_resource_delta(FIXTURE["state"], FIXTURE["delta"])["balance"], 17)

    def test_negative_float_delta_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            apply_resource_delta(FIXTURE["state"], FIXTURE["invalid_delta"])

    def test_failure_does_not_mutate_input_on_negative_balance(self) -> None:
        state = {"balance": 2}
        with self.assertRaises(ValueError):
            apply_resource_delta(state, -3)
        self.assertEqual(state, {"balance": 2})
