from __future__ import annotations

import asyncio
import base64
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from apps.api.app.auth.guest import GuestIdentityService
from packages.domain.identity.repository import InMemoryIdentityRepository


class AcceptingTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return proof == "turnstile-once"


class IdentityE2ETests(unittest.TestCase):
    def test_guest_device_lifecycle_replay_and_rotation(self) -> None:
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes_raw()
        encoded = base64.urlsafe_b64encode(public).rstrip(b"=").decode()
        service = GuestIdentityService(InMemoryIdentityRepository(), AcceptingTurnstile())
        credentials = asyncio.run(service.create("turnstile-once", encoded))
        with self.assertRaisesRegex(ValueError, "turnstile_replay"):
            asyncio.run(service.create("turnstile-once", encoded))
        rotated = service.rotate(credentials.identity_id, credentials.refresh_token)
        self.assertNotEqual(rotated, credentials.refresh_token)
        with self.assertRaisesRegex(ValueError, "credential_invalid"):
            service.rotate(credentials.identity_id, credentials.refresh_token)
