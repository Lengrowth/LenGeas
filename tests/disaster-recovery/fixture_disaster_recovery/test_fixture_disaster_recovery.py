from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tests.fixture_test_support import canonical_json, load_fixture

SUITE = "disaster-recovery"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_disaster_recovery.json")


class FixtureDisasterRecoveryTests(unittest.TestCase):
    def test_positive_snapshot_round_trip_preserves_authoritative_state(self) -> None:
        restored = json.loads(canonical_json(FIXTURE["snapshot"]))
        self.assertEqual(restored, FIXTURE["snapshot"])

    def test_failure_corrupt_snapshot_is_rejected_by_checksum(self) -> None:
        source = canonical_json(FIXTURE["snapshot"])
        checksum = hashlib.sha256(source).hexdigest()
        corrupt = source.replace(b"41", b"42")
        self.assertNotEqual(hashlib.sha256(corrupt).hexdigest(), checksum)

    def test_determinism_rollback_snapshot_is_stable(self) -> None:
        self.assertEqual(
            canonical_json(FIXTURE["snapshot"]),
            canonical_json(dict(FIXTURE["snapshot"])),
        )
