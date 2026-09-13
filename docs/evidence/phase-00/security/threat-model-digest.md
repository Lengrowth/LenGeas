# Threat Model Digest

- Source diagram: `docs/architecture/diagrams/threat-model.mmd`
- Trust-boundary companion: `docs/architecture/diagrams/trust-boundaries.mmd`
- Status: `accepted`
- Digest: recorded in `manifest.json`

## Covered boundaries

- Untrusted clients cannot supply authoritative resulting values.
- Cloudflare edge controls protect the public surface; origin access is authenticated and direct-origin access is denied.
- FastAPI performs final identity, tenancy, authorization, and idempotency checks.
- Definition content, assets, prompts, and retrieval data remain bounded data and cannot introduce executable code.
- AI agents use short-lived scopes and the shared Definition API; publish, approval, secrets, infrastructure, player mutation, and arbitrary network/code access are outside the tool boundary.
- Support access is case-bound, redacted, and audited.
- Durable stores are owned by their services; consumers use events and idempotent actions.

## Required future verification

Phase 03 and Phase 17 must execute authorization, tenant-escape, origin-bypass, asset, formula, AI-scope, secret, and abuse suites. This Phase 00 record is a threat-model review artifact, not a penetration test or external validation.
