from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tests.fixture_test_support import load_fixture

SUITE = "integration"
REQUIRED_DEPENDENCIES = ("docker", "compose-file", "local-stack")
FIXTURE = load_fixture(Path(__file__).parent, "fixture_integration_local_stack.json")


class FixtureIntegrationLocalStackTests(unittest.TestCase):
    def test_positive_local_stack_declares_real_dependency_checks(self) -> None:
        compose = (Path(__file__).parents[2] / ".." / "compose.yaml").resolve()
        self.assertTrue(compose.exists())
        contents = compose.read_text(encoding="utf-8").lower()
        for service in FIXTURE["required_services"]:
            self.assertIn(service, contents)

    def test_failure_missing_docker_is_visible(self) -> None:
        self.assertIsNotNone(shutil.which("docker"), "Docker is mandatory for integration tests")
