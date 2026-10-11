"""Provider-control proofs for linking an external identity."""

from __future__ import annotations

from typing import Protocol

from .jwt import JwtClaims


class VerifiedToken(Protocol):
    async def verify(self, token: str) -> JwtClaims: ...


class SupabaseProviderIdentityVerifier:
    """Verify a separately presented Supabase access token controls its subject."""

    def __init__(self, verifier: VerifiedToken) -> None:
        self.verifier = verifier

    async def verify(self, provider: str, subject: str, proof: str) -> bool:
        if provider != "supabase" or not proof or not subject:
            return False
        try:
            claims = await self.verifier.verify(proof)
        except ValueError:
            return False
        return claims.subject == subject
