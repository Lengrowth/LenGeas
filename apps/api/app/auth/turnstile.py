"""Cloudflare Turnstile server-side verification boundary."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any
from uuid import uuid4

import httpx

from .guest import TurnstileVerifier

__all__ = ["HttpTurnstileVerifier", "TurnstileVerifier"]


class HttpTurnstileVerifier:
    def __init__(
        self,
        secret: str,
        endpoint: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        timeout: float = 3.0,
    ) -> None:
        self._secret = secret
        self.endpoint = endpoint
        self.timeout = timeout
        self._seen: dict[str, float] = {}
        self._lock = Lock()

    async def verify(self, proof: str, remote_ip: str | None = None) -> bool:
        if not proof or len(proof) > 2048:
            return False
        now = time.monotonic()
        with self._lock:
            if proof in self._seen and now - self._seen[proof] < 300:
                return False
        data: dict[str, str] = {
            "secret": self._secret,
            "response": proof,
            "idempotency_key": str(uuid4()),
        }
        if remote_ip:
            data["remoteip"] = remote_ip
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.post(self.endpoint, data=data)
                response.raise_for_status()
                result: Any = response.json()
        except (httpx.HTTPError, ValueError):
            return False
        if not isinstance(result, dict) or result.get("success") is not True:
            return False
        with self._lock:
            if proof in self._seen and now - self._seen[proof] < 300:
                return False
            self._seen[proof] = now
        return True
