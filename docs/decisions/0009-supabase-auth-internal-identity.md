# ADR-0009 — Supabase Auth with internal LenGeas identity

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Identity owner; Security owner
- Supersedes: none
- Superseded by: none

## Context

LenGeas needs email, Apple, Google, MFA, asymmetric JWT verification, guest credentials, universal StudioPlayer identities, identity linking, and tenant-aware authorization without making provider IDs the platform primary key.

## Decision

Use Supabase Auth for external authentication and JWKS. FastAPI verifies signature, issuer, audience, expiry, not-before, and key ID, then maps `sub` to internal accounts. Guest and StudioPlayer identities remain LenGeas-owned and all authorization is evaluated by the platform policy decision point.

## Consequences

The design separates external authentication from internal identity and supports provider changes. It requires JWKS cache and rotation drills, guest abuse controls, merge idempotency, and provider outage behavior.

## Rejected designs

- Provider IDs as platform primary keys: rejected because internal identity must survive provider changes and guest linking.
- Edge-only authorization: rejected because final authorization belongs at the origin policy decision point.

## Validation

JWT negative cases, key rotation, guest challenge replay, identity merge collisions, role matrices, provider outage, and PII deletion tests are required before production rollout.

## Rollout and reversal

Create internal identity mappings before enabling sign-in, migrate providers through dual verification where needed, and revoke prior keys only after validation. Provider replacement requires an identity migration plan and superseding ADR.
