from __future__ import annotations

import asyncio
import base64
import json
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.api.app.auth.jwt import HttpJwksTransport, SupabaseJwtVerifier
from apps.api.app.auth.turnstile import HttpTurnstileVerifier


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
