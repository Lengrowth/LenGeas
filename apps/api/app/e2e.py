"""Provider-independent HTTP API used only by the hosted E2E gate."""

from __future__ import annotations

from apps.api.app.main import create_app


class HostedTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return proof == "ci-e2e-proof"


app = create_app(test_mode=True, turnstile=HostedTurnstile())
