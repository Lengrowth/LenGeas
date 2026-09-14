# Phase 03 decisions

- Preserve ADR-0009: Supabase remains the external authentication provider and LenGeas owns internal identity.
- Preserve ADR-0011: development uses synthetic data and no new provider or production infrastructure is activated.
- Use a trusted scope value minted after policy evaluation for every tenant-owned repository operation.
- Use PyJWT asymmetric verification with an HTTP JWKS cache, forced refresh on unknown `kid`, and explicit revocation state.
- Use a rollback snapshot in the deterministic test repository and a MongoDB transaction boundary for merge persistence.
