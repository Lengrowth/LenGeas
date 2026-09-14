from __future__ import annotations

import os
import unittest
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from tests.fixture_test_support import load_fixture

SUITE = "e2e"
REQUIRED_DEPENDENCIES = ("e2e-base-url", "e2e-guest-proof", "e2e-device-key")
FIXTURE = load_fixture(Path(__file__).parent, "fixture_e2e_publish_flow.json")


class FixtureE2EPublishFlowTests(unittest.TestCase):
    def test_positive_synthetic_workflow_is_ordered(self) -> None:
        self.assertEqual(FIXTURE["workflow"][:3], ["draft", "validate", "publish"])
        self.assertIn("rollback", FIXTURE["workflow"])

    def test_failure_health_endpoint_is_reachable(self) -> None:
        base_url = os.environ["LENGEAS_E2E_BASE_URL"].rstrip("/") + "/"
        request = Request(  # noqa: S310 - URL is operator-supplied.
            urljoin(base_url, FIXTURE["health_path"]), method="GET"
        )
        with urlopen(request, timeout=5) as response:  # noqa: S310 - URL is operator-supplied.
            self.assertLess(response.status, 500)
