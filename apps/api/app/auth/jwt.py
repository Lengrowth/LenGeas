"""Supabase-compatible asymmetric JWT verification.

The verifier performs a real JWKS HTTP fetch when a key is not cached.  Tests
can provide a transport boundary, but they still exercise PyJWT's asymmetric
signature verification and claim validation.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import jwt
from jwt import PyJWK


class JwksTransport(Protocol):
    async def get(self, url: str) -> dict[str, Any]: ...


class HttpJwksTransport:
    async def get(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=5.0, follow_redirects=False, trust_env=False
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            value = response.json()
        if not isinstance(value, dict) or not isinstance(value.get("keys"), list):
            raise ValueError("invalid_jwks_document")
        return value


@dataclass(frozen=True, slots=True)
class JwtClaims:
    subject: str
    issuer: str
    audience: str | list[str]
    jwt_id: str | None
    raw: dict[str, Any]


class SupabaseJwtVerifier:
    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: str,
        *,
        ttl_seconds: int = 300,
        leeway_seconds: int = 5,
        transport: JwksTransport | None = None,
    ) -> None:
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self.ttl_seconds = ttl_seconds
        self.leeway_seconds = leeway_seconds
        self.transport = transport or HttpJwksTransport()
        self._keys: dict[str, dict[str, Any]] = {}
        self._fetched_at = 0.0
        self._revoked_jti: set[str] = set()
        self._revoked_subject_epoch: dict[str, int] = {}
        self._subject_epochs: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def refresh(self, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and self._keys and now - self._fetched_at < self.ttl_seconds:
            return
        async with self._lock:
            if not force and self._keys and time.monotonic() - self._fetched_at < self.ttl_seconds:
                return
            document = await self.transport.get(self.jwks_url)
            keys = {
                str(key["kid"]): key
                for key in document["keys"]
                if isinstance(key, dict) and key.get("kid")
            }
            if not keys:
                raise ValueError("empty_jwks")
            self._keys = keys
            self._fetched_at = time.monotonic()

    async def verify(self, token: str) -> JwtClaims:
        if not token or len(token) > 16_384:
            raise ValueError("malformed_token")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as error:
            raise ValueError("malformed_token") from error
        algorithm = header.get("alg")
        kid = header.get("kid")
        if algorithm not in {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}:
            raise ValueError("algorithm_not_allowed")
        if not isinstance(kid, str) or not kid:
            raise ValueError("unknown_kid")
        await self.refresh()
        key = self._keys.get(kid)
        if key is None:
            await self.refresh(force=True)
            key = self._keys.get(kid)
        if key is None:
            raise ValueError("unknown_kid")
        if key.get("alg") and key["alg"] != algorithm:
            raise ValueError("algorithm_key_mismatch")
        try:
            claims = jwt.decode(
                token,
                PyJWK.from_dict(key).key,
                algorithms=[algorithm],
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway_seconds,
                options={"require": ["sub", "iss", "aud", "exp", "iat"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise ValueError("token_expired") from error
        except jwt.ImmatureSignatureError as error:
            raise ValueError("token_not_yet_valid") from error
        except jwt.InvalidIssuerError as error:
            raise ValueError("wrong_issuer") from error
        except jwt.InvalidAudienceError as error:
            raise ValueError("wrong_audience") from error
        except jwt.InvalidSignatureError as error:
            raise ValueError("invalid_signature") from error
        except jwt.InvalidTokenError as error:
            raise ValueError("invalid_token") from error
        subject = str(claims["sub"])
        jwt_id = str(claims["jti"]) if claims.get("jti") else None
        if jwt_id and jwt_id in self._revoked_jti:
            raise ValueError("token_revoked")
        token_epoch = int(claims.get("session_epoch", 0))
        if token_epoch < self._revoked_subject_epoch.get(subject, -1):
            raise ValueError("token_revoked")
        return JwtClaims(subject, str(claims["iss"]), claims["aud"], jwt_id, claims)

    def revoke_jti(self, jwt_id: str) -> None:
        self._revoked_jti.add(jwt_id)

    def revoke_subject(self, subject: str) -> None:
        next_epoch = self._subject_epochs.get(subject, 0) + 1
        self._subject_epochs[subject] = next_epoch
        self._revoked_subject_epoch[subject] = next_epoch

    def clear_cache(self) -> None:
        self._keys = {}
        self._fetched_at = 0.0

    def cache_state(self) -> dict[str, int]:
        return {"keys": len(self._keys), "revoked_jti": len(self._revoked_jti)}
