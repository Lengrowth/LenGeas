from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from packages.domain.providers.store_receipts import (
    AppleStoreKitAdapter,
    GooglePlayAdapter,
    ProviderError,
)


def _apple_keys() -> tuple[ec.EllipticCurvePrivateKey, bytes, bytes]:
    now = datetime.now(UTC).replace(tzinfo=None)
    root_key = ec.generate_private_key(ec.SECP256R1())
    root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-root")])
    root = (
        x509.CertificateBuilder()
        .subject_name(root_name)
        .issuer_name(root_name)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .sign(root_key, hashes.SHA256())
    )
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "app-store-signer")]))
        .issuer_name(root.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=5))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )
    cert = base64.b64encode(leaf.public_bytes(serialization.Encoding.DER)).decode()
    return leaf_key, root.public_bytes(serialization.Encoding.PEM), cert.encode()


def _apple_jws(key: ec.EllipticCurvePrivateKey, cert: bytes, claims: dict[str, object]) -> str:
    return jwt.encode(claims, key, algorithm="ES256", headers={"x5c": [cert.decode()]})


def test_apple_server_api_receipt_and_signed_webhook_contract() -> None:
    key, root, cert = _apple_keys()
    transaction = _apple_jws(
        key,
        cert,
        {
            "transactionId": "12345",
            "productId": "coins",
            "bundleId": "com.example.game",
            "purchaseDate": 1_790_000_000_000,
            "environment": "Sandbox",
        },
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer server-api-token"
        return httpx.Response(200, json={"signedTransactionInfo": transaction})

    adapter = AppleStoreKitAdapter(
        base_url="https://sandbox.storekit.example",
        bearer_token="server-api-token",
        bundle_id="com.example.game",
        trusted_root_certificates=(root,),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    purchase = asyncio_call(
        adapter.verify_purchase(
            transaction_id="12345", product_id="coins", player_id="p", game_id="g", studio_id="s"
        )
    )
    assert purchase.provider == "apple"
    assert purchase.environment == "sandbox"
    assert purchase.product_id == "coins"
    webhook_token = _apple_jws(
        key,
        cert,
        {
            "notificationUUID": "event-1",
            "notificationType": "REFUND",
            "data": {"signedTransactionInfo": transaction},
        },
    )
    event = adapter.verify_webhook(webhook_token)
    assert event.event_id == "event-1"
    assert event.transaction_id == "12345"
    with pytest.raises(ProviderError, match="apple_signed_payload_signature_invalid"):
        adapter.verify_webhook(webhook_token[:-2] + "xx")


def asyncio_call(awaitable):
    import asyncio

    return asyncio.run(awaitable)


def test_google_play_valid_and_pending_purchase_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer google-token"
        state = 0 if "valid-token" in request.url.path else 2
        return httpx.Response(
            200,
            json={
                "purchaseState": state,
                "productId": "coins",
                "orderId": "GPA.1",
                "purchaseTimeMillis": "1790000000000",
            },
        )

    adapter = GooglePlayAdapter(
        package_name="com.example.game",
        access_token="google-token",
        expected_push_audience="https://api.example.com/google-webhook",
        expected_push_email="pubsub@example.iam.gserviceaccount.com",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    purchase = asyncio_call(
        adapter.verify_product_purchase(
            product_id="coins",
            purchase_token="valid-token",
            player_id="p",
            game_id="g",
            studio_id="s",
        )
    )
    assert purchase.provider_transaction_id == "GPA.1"
    with pytest.raises(ProviderError, match="google_purchase_not_verified"):
        asyncio_call(
            adapter.verify_product_purchase(
                product_id="coins",
                purchase_token="pending-token",
                player_id="p",
                game_id="g",
                studio_id="s",
            )
        )


def test_google_pubsub_webhook_authentication_and_event_identity() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "google-key-1"
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk["kid"] = kid
    token = jwt.encode(
        {
            "iss": "https://accounts.google.com",
            "aud": "https://api.example.com/google-webhook",
            "email": "pubsub@example.iam.gserviceaccount.com",
            "email_verified": True,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        key,
        algorithm="RS256",
        headers={"kid": kid},
    )
    data = base64.b64encode(
        json.dumps(
            {"notificationType": "ONE_TIME_PRODUCT_PURCHASED", "purchaseToken": "tok"}
        ).encode()
    ).decode()

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"keys": [jwk]})

    adapter = GooglePlayAdapter(
        package_name="com.example.game",
        access_token="google-token",
        expected_push_audience="https://api.example.com/google-webhook",
        expected_push_email="pubsub@example.iam.gserviceaccount.com",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    event = asyncio_call(
        adapter.verify_webhook(f"Bearer {token}", {"message": {"messageId": "msg-1", "data": data}})
    )
    assert event.event_id == "msg-1"
    assert event.transaction_id == "tok"
    with pytest.raises(ProviderError, match="google_webhook_authentication_failed"):
        asyncio_call(
            adapter.verify_webhook(
                "Bearer invalid", {"message": {"messageId": "msg-1", "data": data}}
            )
        )
