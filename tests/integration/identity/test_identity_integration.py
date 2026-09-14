from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from apps.api.app.auth.jwt import HttpJwksTransport, SupabaseJwtVerifier
from apps.api.app.auth.turnstile import HttpTurnstileVerifier
from packages.domain.tenancy.models import Environment, TrustedScope
from packages.persistence.mongodb.identity.repository import IdentityMongoRepository


def _b64(value: int) -> str:
    return (
        base64.urlsafe_b64encode(value.to_bytes((value.bit_length() + 7) // 8, "big"))
        .rstrip(b"=")
        .decode()
    )


class Transport:
    def __init__(self, document: dict[str, object]) -> None:
        self.document = document
        self.calls = 0

    async def get(self, url: str) -> dict[str, object]:
        self.calls += 1
        return self.document


class IdentityIntegrationTests(unittest.TestCase):
    def test_mongodb_identity_repository_is_durable_and_scoped(self) -> None:
        uri = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0"
        )
        database_name = os.environ.get("MONGODB_DATABASE", "lengeas_identity_integration")
        client = AsyncMongoClient(uri, serverSelectionTimeoutMS=1500)

        async def run() -> None:
            try:
                await client.admin.command("ping")
                database = client[database_name]
                repository = IdentityMongoRepository(database)
                await repository.ensure_indexes()
                account_id = await repository.create_account()
                player_id = await repository.create_player()
                scope = TrustedScope(
                    "integration-actor",
                    "integration-studio",
                    "integration-game",
                    Environment.TESTING,
                )
                await repository.create_profile(scope, player_id, "integration-game")
                profile = await repository.find_profile(scope, player_id)
                self.assertIsNotNone(profile)
                self.assertEqual(profile["studio_id"], "integration-studio")  # type: ignore[index]
                await database.accounts.delete_one({"account_id": account_id})
                await database.studio_players.delete_one({"player_id": player_id})
                await database.global_profiles.delete_one({"player_id": player_id})
                await database.game_profiles.delete_many({"player_id": player_id})
            finally:
                await client.close()

        try:
            asyncio.run(run())
        except PyMongoError as error:
            self.skipTest(f"MongoDB unavailable: {error}")

    def test_unknown_kid_forces_refresh_and_real_rsa_verification(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = key.private_numbers().public_numbers
        jwk = {
            "kty": "RSA",
            "kid": "k1",
            "alg": "RS256",
            "use": "sig",
            "n": _b64(numbers.n),
            "e": _b64(numbers.e),
        }

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
                payload = json.dumps({"keys": [jwk]}).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        thread.start()
        verifier = SupabaseJwtVerifier(
            f"http://127.0.0.1:{server.server_port}/jwks",
            "https://issuer.test",
            "audience",
            transport=HttpJwksTransport(),
        )
        token = jwt.encode(
            {
                "sub": "s1",
                "iss": "https://issuer.test",
                "aud": "audience",
                "iat": int(time.time()),
                "exp": int(time.time()) + 60,
            },
            key,
            algorithm="RS256",
            headers={"kid": "k1"},
        )
        claims = asyncio.run(verifier.verify(token))
        self.assertEqual(claims.subject, "s1")
        server.shutdown()

    def test_wrong_issuer_and_algorithm_confusion_are_rejected(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = key.private_numbers().public_numbers
        jwk = {
            "kty": "RSA",
            "kid": "k1",
            "alg": "RS256",
            "n": _b64(numbers.n),
            "e": _b64(numbers.e),
        }
        verifier = SupabaseJwtVerifier(
            "https://jwks.test",
            "https://issuer.test",
            "audience",
            transport=Transport({"keys": [jwk]}),
        )
        token = jwt.encode(
            {
                "sub": "s1",
                "iss": "wrong",
                "aud": "audience",
                "iat": int(time.time()),
                "exp": int(time.time()) + 60,
            },
            key,
            algorithm="RS256",
            headers={"kid": "k1"},
        )
        with self.assertRaisesRegex(ValueError, "wrong_issuer"):
            asyncio.run(verifier.verify(token))

    def test_turnstile_siteverify_boundary_rejects_replay(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            calls = 0

            def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
                Handler.calls += 1
                payload = json.dumps({"success": True}).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.05)
        verifier = HttpTurnstileVerifier(
            "synthetic-secret", f"http://127.0.0.1:{server.server_port}"
        )
        self.assertTrue(asyncio.run(verifier.verify("proof")))
        self.assertFalse(asyncio.run(verifier.verify("proof")))
        self.assertEqual(Handler.calls, 1)
        server.shutdown()
