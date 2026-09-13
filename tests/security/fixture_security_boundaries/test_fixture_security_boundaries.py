from __future__ import annotations

import unittest
from pathlib import Path

from tests.fixture_test_support import load_fixture, redact, tenant_read

SUITE = "security"
REQUIRED_DEPENDENCIES: tuple[str, ...] = ()
FIXTURE = load_fixture(Path(__file__).parent, "fixture_security_boundaries.json")


class FixtureSecurityBoundaryTests(unittest.TestCase):
    def test_security_same_tenant_read_is_allowed(self) -> None:
        self.assertEqual(
            tenant_read(FIXTURE["actor_tenant"], FIXTURE["actor_tenant"], FIXTURE["records"]),
            {"balance": 3},
        )

    def test_negative_cross_tenant_read_is_denied(self) -> None:
        with self.assertRaises(PermissionError):
            tenant_read(FIXTURE["actor_tenant"], FIXTURE["other_tenant"], FIXTURE["records"])

    def test_security_redacts_token_before_logging(self) -> None:
        redacted = redact(FIXTURE["log_event"])
        self.assertEqual(redacted["token"], "[REDACTED]")
        self.assertNotIn("synthetic-secret", str(redacted))
