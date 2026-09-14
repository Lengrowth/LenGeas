from __future__ import annotations

import os
import unittest

import httpx


class IdentityE2ETests(unittest.TestCase):
    def test_guest_lifecycle_through_deployed_api_boundary(self) -> None:
        base_url = os.environ.get("LENGEAS_E2E_BASE_URL", "").rstrip("/")
        proof = os.environ.get("LENGEAS_E2E_GUEST_PROOF", "")
        device_key = os.environ.get("LENGEAS_E2E_DEVICE_PUBLIC_KEY", "")
        if not base_url or not proof or not device_key:
            self.skipTest("deployed API E2E prerequisites are unavailable")
        headers = {"Idempotency-Key": "e2e-guest-lifecycle-0001"}
        payload = {"turnstile_proof": proof, "device_public_key": device_key}
        with httpx.Client(base_url=base_url, timeout=10.0, trust_env=False) as client:
            first = client.post("/api/v1/auth/guests", json=payload, headers=headers)
            self.assertEqual(first.status_code, 201, first.text)
            replay = client.post("/api/v1/auth/guests", json=payload, headers=headers)
        self.assertEqual(replay.status_code, 201, replay.text)
        self.assertEqual(replay.json(), first.json())
