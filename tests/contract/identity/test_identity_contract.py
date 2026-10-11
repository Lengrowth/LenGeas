from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


class IdentityContractTests(unittest.TestCase):
    def test_event_schema_rejects_unknown_fields(self) -> None:
        schema = json.loads(Path("packages/schemas/api/v1/events.json").read_text(encoding="utf-8"))
        invalid = {
            "event_id": "e",
            "type": "identity.linked.v1",
            "occurred_at": "2030-01-01T00:00:00Z",
            "producer": "identity",
            "studio_id": None,
            "correlation_id": "c",
            "payload": {},
            "token": "secret",
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))

    def test_openapi_is_31_and_has_merge_operations(self) -> None:
        document = json.loads(
            Path("packages/schemas/api/v1/openapi.json").read_text(encoding="utf-8")
        )
        self.assertEqual(document["openapi"], "3.1.0")
        self.assertIn("/api/v1/players/merge", document["paths"])
