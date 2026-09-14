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

    def test_phase03_lifecycle_through_deployed_api_boundary(self) -> None:
        base_url = os.environ.get("LENGEAS_E2E_BASE_URL", "").rstrip("/")
        proof = os.environ.get("LENGEAS_E2E_LIFECYCLE_PROOF", "")
        device_key = os.environ.get("LENGEAS_E2E_LIFECYCLE_DEVICE_PUBLIC_KEY", "")
        token = os.environ.get("LENGEAS_E2E_TOKEN", "")
        if not base_url or not proof or not device_key or not token:
            self.skipTest("deployed API E2E prerequisites are unavailable")
        auth = {"Authorization": f"Bearer {token}", "x-studio-id": "ci-e2e-studio"}
        with httpx.Client(base_url=base_url, timeout=10.0, trust_env=False) as client:
            metadata = client.get("/__e2e/metadata").json()
            current = client.get("/api/v1/auth/current", headers=auth)
            self.assertEqual(current.status_code, 200, current.text)
            target_player_id = current.json()["player_id"]

            guest = client.post(
                "/api/v1/auth/guests",
                json={"turnstile_proof": proof, "device_public_key": device_key},
                headers={**auth, "Idempotency-Key": "e2e-full-guest-0001"},
            )
            self.assertEqual(guest.status_code, 201, guest.text)
            guest_data = guest.json()
            rotated = client.post(
                "/api/v1/auth/credentials/rotate",
                json={
                    "identity_id": guest_data["identity_id"],
                    "refresh_token": guest_data["refresh_token"],
                },
                headers={**auth, "Idempotency-Key": "e2e-full-rotate-0001"},
            )
            self.assertEqual(rotated.status_code, 200, rotated.text)

            linked = client.post(
                "/api/v1/auth/identity-links",
                json={
                    "provider": "supabase",
                    "subject": "ci-linked-subject",
                    "provider_proof": "ci-provider-proof",
                },
                headers={**auth, "Idempotency-Key": "e2e-full-link-0001"},
            )
            self.assertEqual(linked.status_code, 201, linked.text)

            preview = client.post(
                "/api/v1/players/merge/preview",
                json={
                    "source_player_id": metadata["source_player_id"],
                    "target_player_id": target_player_id,
                    "source_credential": metadata["source_credential"],
                },
                headers={**auth, "Idempotency-Key": "e2e-full-merge-preview-0001"},
            )
            self.assertEqual(preview.status_code, 200, preview.text)
            merge = client.post(
                "/api/v1/players/merge",
                json={
                    "preview_id": preview.json()["preview_id"],
                    "choices": {"ci-e2e-game": "target"},
                    "idempotency_key": "e2e-full-merge-0001",
                    "source_credential": metadata["source_credential"],
                },
                headers={**auth, "Idempotency-Key": "e2e-full-merge-0001"},
            )
            self.assertEqual(merge.status_code, 200, merge.text)

            correction = client.post(
                "/api/v1/accounts/correction",
                headers={**auth, "Idempotency-Key": "e2e-full-correction-0001"},
            )
            self.assertEqual(correction.status_code, 202, correction.text)

            membership = client.post(
                "/api/v1/studios/memberships",
                json={"account_id": metadata["secondary_account_id"], "role": "viewer"},
                headers={**auth, "Idempotency-Key": "e2e-full-membership-0001"},
            )
            self.assertEqual(membership.status_code, 201, membership.text)
            role = client.post(
                "/api/v1/studios/memberships/role",
                json={"membership_id": membership.json()["membership_id"], "role": "analyst"},
                headers={**auth, "Idempotency-Key": "e2e-full-role-0001"},
            )
            self.assertEqual(role.status_code, 200, role.text)

            service = client.post(
                "/api/v1/studios/service-accounts",
                json={"name": "e2e-worker", "scopes": ["player:read"]},
                headers={**auth, "Idempotency-Key": "e2e-full-service-0001"},
            )
            self.assertEqual(service.status_code, 201, service.text)
            revoked = client.post(
                "/api/v1/studios/service-accounts/revoke",
                params={"service_account_id": service.json()["service_account_id"]},
                headers={**auth, "Idempotency-Key": "e2e-full-service-revoke-0001"},
            )
            self.assertEqual(revoked.status_code, 204, revoked.text)

            deletion = client.post(
                "/api/v1/accounts/deletion",
                headers={**auth, "Idempotency-Key": "e2e-full-deletion-0001"},
            )
            self.assertEqual(deletion.status_code, 202, deletion.text)
            self.assertEqual(client.get("/api/v1/auth/current", headers=auth).status_code, 401)
