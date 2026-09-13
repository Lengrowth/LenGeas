# Phase 03 — Identity, Tenancy, and Authorization

## Goal

Deliver universal player identity, guest conversion, studio tenancy, machine identity, and centralized authorization.

## Entry

Phase 02 is accepted.

## Tasks

- [ ] **P03-T01 — Implement identity models.** Create account, StudioPlayer, identity link, game profile, global profile, studio, membership, service account, and audit schemas/repositories. Evidence: model and index tests.
- [ ] **P03-T02 — Integrate Supabase JWT.** Verify asymmetric JWKS, issuer, audience, expiry, rotation, revocation cache purge, and internal account mapping. Depends on P03-T01. Evidence: key-rotation drill.
- [ ] **P03-T03 — Implement guest identity.** Deliver Turnstile-protected guest creation, device keys, token rotation, abuse limits, and recovery. Depends on P03-T01, P02-T06. Evidence: device lifecycle E2E.
- [ ] **P03-T04 — Implement guest merge.** Build preview, no-conflict automatic merge, per-game conflict selection, entitlement handling, idempotency, and rollback-before-commit. Depends on P03-T03. Evidence: merge matrix tests.
- [ ] **P03-T05 — Implement authorization service.** Centralize RBAC/ABAC, tenant/game scope, environment, ownership, support-case grants, AI scopes, and policy explanations. Depends on P03-T01. Evidence: authorization matrix.
- [ ] **P03-T06 — Implement studio administration.** Membership invitations, role changes, service accounts, credential revocation, MFA enforcement, and audit. Depends on P03-T02, P03-T05. Evidence: admin E2E.
- [ ] **P03-T07 — Implement account rights.** Export, correction, deletion, legal hold, session revocation, and tombstone workflows. Depends on P03-T02. Evidence: privacy lifecycle report.
- [ ] **P03-T08 — Red-team isolation.** Test horizontal/vertical escalation, provider-link takeover, guest replay, cross-studio/game access, support abuse, and service-account scope. Depends on P03-T02–T07. Evidence: zero high findings.

## Exit gate

All identity paths, roles, guests, merges, service accounts, privacy workflows, and audit events pass E2E tests; tenant escape and role escalation suites report zero failures.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 02 handoff, ADR 0009, and the data, identity, API, and security contracts.

### Exact outputs

`packages/domain/{identity,tenancy}/`; `packages/persistence/mongodb/{identity,tenancy,audit}/`; `apps/api/app/{auth,users,players,studios,permissions,audit}/`; API schemas under `packages/schemas/api/v1/{auth,players,studios,permissions}/`; tests under every test layer's `identity/`; and runbooks for Supabase key rotation, identity merge, deletion, and authorization incident.

At exit the API exposes guest creation, identity link, merge preview/commit, current account, session revocation, studio/membership/service-account CRUD, and privacy operations. It publishes `identity.guest_created.v1`, `identity.linked.v1`, `identity.merged.v1`, `studio.membership_changed.v1`, and `privacy.requested.v1`. Create unique indexes for provider subject, guest device key, membership, service client ID, and merge idempotency.

### Required negative tests

Reject expired/wrong issuer/wrong audience/unknown-kid/revoked JWTs; rotate a live asymmetric key; replay Turnstile and guest tokens; steal/replace a device key; run every merge collision and repeated/concurrent merge; generate every role × resource × action × environment allow/deny case; guess object IDs across two studios and games; forge scope claims; misuse support access; and prove PII deletion with pseudonymized required financial history.

Run `task test:unit -- identity`, `task test:property -- identity`, `task test:contract -- auth`, `task test:integration -- supabase,mongodb`, `task test:e2e -- identity`, `task test:security -- tenancy,authorization`, and the phase gate.

### Handoff to Phase 04

Provide actor/scope types, policy-decision interface, tenant-scoped repository contract, event-envelope identity fields, collection/index manifest, OpenAPI digest, test-tenant command, and definition-ownership authorization rules.
