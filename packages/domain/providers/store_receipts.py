"""Fail-closed Apple App Store Server API and Google Play receipt adapters."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import httpx
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from packages.domain.entitlements import VerifiedPurchase


class ProviderError(ValueError):
    """Provider authentication, response, or receipt validation failed."""


@dataclass(frozen=True, slots=True)
class ProviderWebhook:
    provider: str
    event_id: str
    transaction_id: str | None
    event_type: str
    payload_digest: str
    occurred_at: datetime


class GooglePushAuthenticator(Protocol):
    async def verify(self, authorization: str) -> Mapping[str, Any]: ...


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _verify_apple_jws(token: str, trusted_roots: tuple[bytes, ...]) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3 or not trusted_roots:
        raise ProviderError("apple_signed_payload_invalid")
    try:
        header = json.loads(_b64url_decode(parts[0]))
        if header.get("alg") != "ES256" or not header.get("x5c"):
            raise ProviderError("apple_certificate_chain_missing")
        chain = [
            x509.load_der_x509_certificate(base64.b64decode(encoded)) for encoded in header["x5c"]
        ]
        roots = [x509.load_pem_x509_certificate(root) for root in trusted_roots]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise ProviderError("apple_signed_payload_invalid") from error
    now = datetime.now(UTC)
    for cert in chain:
        if cert.not_valid_before_utc > now or cert.not_valid_after_utc <= now:
            raise ProviderError("apple_signing_certificate_expired")
    for child, issuer in zip(chain, chain[1:], strict=False):
        try:
            child.verify_directly_issued_by(issuer)
        except (ValueError, TypeError) as error:
            raise ProviderError("apple_certificate_chain_invalid") from error
    last = chain[-1]
    trusted = next(
        (
            root
            for root in roots
            if root.fingerprint(hashes.SHA256()) == last.fingerprint(hashes.SHA256())
        ),
        None,
    )
    if trusted is None:
        trusted = next((root for root in roots if last.issuer == root.subject), None)
        if trusted is None:
            raise ProviderError("apple_certificate_untrusted")
        try:
            last.verify_directly_issued_by(trusted)
        except (ValueError, TypeError) as error:
            raise ProviderError("apple_certificate_chain_invalid") from error
    public_key = chain[0].public_key()
    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise ProviderError("apple_signing_key_invalid")
    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            options={"verify_aud": False, "verify_exp": False},
        )
    except jwt.PyJWTError as error:
        raise ProviderError("apple_signed_payload_signature_invalid") from error
    return claims


class AppleStoreKitAdapter:
    """Uses Apple's server API and verifies returned JWS against configured roots."""

    def __init__(
        self,
        *,
        base_url: str,
        bearer_token: str,
        bundle_id: str,
        trusted_root_certificates: tuple[bytes, ...],
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not (
            base_url.startswith("https://")
            and bearer_token
            and bundle_id
            and trusted_root_certificates
        ):
            raise ProviderError("apple_provider_configuration_invalid")
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.bundle_id = bundle_id
        self.trusted_roots = trusted_root_certificates
        self.client = client or httpx.AsyncClient(timeout=10.0)

    async def verify_purchase(
        self,
        *,
        transaction_id: str,
        product_id: str,
        player_id: str,
        game_id: str,
        studio_id: str,
    ) -> VerifiedPurchase:
        if not transaction_id.isdecimal():
            raise ProviderError("apple_transaction_id_invalid")
        response = await self.client.get(
            f"{self.base_url}/inApps/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {self.bearer_token}"},
        )
        if response.status_code != 200:
            raise ProviderError("apple_transaction_lookup_failed")
        payload = response.json()
        signed = payload.get("signedTransactionInfo")
        if not isinstance(signed, str):
            raise ProviderError("apple_transaction_unverified")
        claims = _verify_apple_jws(signed, self.trusted_roots)
        if claims.get("transactionId") != transaction_id or claims.get("productId") != product_id:
            raise ProviderError("apple_transaction_mismatch")
        if claims.get("bundleId") != self.bundle_id:
            raise ProviderError("apple_bundle_mismatch")
        purchased_at = datetime.fromtimestamp(int(claims["purchaseDate"]) / 1000, UTC)
        expires = claims.get("expiresDate")
        return VerifiedPurchase(
            "apple",
            transaction_id,
            product_id,
            player_id,
            game_id,
            studio_id,
            purchased_at,
            datetime.fromtimestamp(int(expires) / 1000, UTC) if expires is not None else None,
            "sandbox" if claims.get("environment") == "Sandbox" else "production",
        )

    def verify_webhook(self, signed_payload: str) -> ProviderWebhook:
        claims = _verify_apple_jws(signed_payload, self.trusted_roots)
        event_id = claims.get("notificationUUID")
        event_type = claims.get("notificationType")
        data = claims.get("data", {})
        transaction_id = None
        signed_transaction = data.get("signedTransactionInfo") if isinstance(data, dict) else None
        if isinstance(signed_transaction, str):
            transaction_id = _verify_apple_jws(signed_transaction, self.trusted_roots).get(
                "transactionId"
            )
        if not isinstance(event_id, str) or not isinstance(event_type, str):
            raise ProviderError("apple_webhook_invalid")
        return ProviderWebhook(
            "apple",
            event_id,
            transaction_id,
            event_type,
            hashlib.sha256(signed_payload.encode()).hexdigest(),
            datetime.now(UTC),
        )


class GooglePlayAdapter:
    """Verifies product/subscription tokens through the Google Play Developer API."""

    def __init__(
        self,
        *,
        package_name: str,
        access_token: str,
        expected_push_audience: str,
        expected_push_email: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not all((package_name, access_token, expected_push_audience, expected_push_email)):
            raise ProviderError("google_provider_configuration_invalid")
        self.package_name = package_name
        self.access_token = access_token
        self.expected_push_audience = expected_push_audience
        self.expected_push_email = expected_push_email
        self.client = client or httpx.AsyncClient(timeout=10.0)

    async def verify_product_purchase(
        self,
        *,
        product_id: str,
        purchase_token: str,
        player_id: str,
        game_id: str,
        studio_id: str,
    ) -> VerifiedPurchase:
        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{self.package_name}/purchases/products/{product_id}/tokens/{purchase_token}"
        )
        response = await self.client.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise ProviderError("google_purchase_lookup_failed")
        value = response.json()
        if value.get("purchaseState") != 0 or value.get("productId", product_id) != product_id:
            raise ProviderError("google_purchase_not_verified")
        order_id = value.get("orderId")
        if not isinstance(order_id, str) or not order_id:
            raise ProviderError("google_order_id_missing")
        purchased_ms = int(value["purchaseTimeMillis"])
        return VerifiedPurchase(
            "google",
            order_id,
            product_id,
            player_id,
            game_id,
            studio_id,
            datetime.fromtimestamp(purchased_ms / 1000, UTC),
            None,
            "production",
        )

    async def verify_push_authorization(self, authorization: str) -> Mapping[str, Any]:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise ProviderError("google_webhook_authentication_required")
        try:
            header = jwt.get_unverified_header(token)
            response = await self.client.get("https://www.googleapis.com/oauth2/v3/certs")
            response.raise_for_status()
            keys = response.json().get("keys", [])
            jwk = next(key for key in keys if key.get("kid") == header.get("kid"))
            claims = jwt.decode(
                token,
                jwt.PyJWK.from_dict(jwk).key,
                algorithms=[header["alg"]],
                audience=self.expected_push_audience,
                issuer=["accounts.google.com", "https://accounts.google.com"],
            )
        except (httpx.HTTPError, jwt.PyJWTError, StopIteration, KeyError, ValueError) as error:
            raise ProviderError("google_webhook_authentication_failed") from error
        if (
            claims.get("email") != self.expected_push_email
            or claims.get("email_verified") is not True
        ):
            raise ProviderError("google_webhook_identity_mismatch")
        return cast(Mapping[str, Any], claims)

    async def verify_webhook(self, authorization: str, body: Mapping[str, Any]) -> ProviderWebhook:
        await self.verify_push_authorization(authorization)
        message = body.get("message")
        if not isinstance(message, Mapping) or not isinstance(message.get("data"), str):
            raise ProviderError("google_webhook_invalid")
        try:
            decoded = json.loads(base64.b64decode(message["data"], validate=True))
        except (ValueError, json.JSONDecodeError) as error:
            raise ProviderError("google_webhook_invalid") from error
        event_id = message.get("messageId")
        event_type = decoded.get("notificationType", "purchase_notification")
        transaction = decoded.get("purchaseToken")
        if not isinstance(event_id, str) or not isinstance(event_type, str):
            raise ProviderError("google_webhook_invalid")
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        return ProviderWebhook(
            "google",
            event_id,
            transaction if isinstance(transaction, str) else None,
            event_type,
            hashlib.sha256(canonical).hexdigest(),
            datetime.now(UTC),
        )
