from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.fixture_test_support import canonical_json, load_fixture

SUITE = "contract"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_contract_schema.json")


class FixtureContractSchemaTests(unittest.TestCase):
    def test_positive_error_envelope_has_stable_wire_fields(self) -> None:
        self.assertEqual(set(FIXTURE["error"]), {"code", "retryable"})
        self.assertIsInstance(FIXTURE["error"]["retryable"], bool)

    def test_negative_event_type_without_major_version_is_invalid(self) -> None:
        self.assertIsNone(re.fullmatch(r"[a-z_]+\.[a-z_]+\.v[0-9]+", "platform.state_changed"))

    def test_failure_unknown_contract_field_changes_canonical_shape(self) -> None:
        base = canonical_json(FIXTURE["error"])
        changed = canonical_json({**FIXTURE["error"], "unknown": True})
        self.assertNotEqual(base, changed)
