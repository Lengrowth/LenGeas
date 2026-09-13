# Phase 07 — Progression and SDKs

## Goal

Deliver universal progression domains and generated client/server SDKs that expose the stable platform contracts.

## Entry

Phase 06 is accepted.

## Tasks

- [ ] **P07-T01 — Implement progression graphs.** Build unlocks, dependencies, exclusive branches, repeat policies, reachability, action integration, and graph projections. Evidence: graph property suite.
- [ ] **P07-T02 — Implement quests.** Build quest lifecycle, objectives, counters, subscriptions, deadlines, claims, and definition pinning. Depends on P07-T01, P05-T07. Evidence: event/order/duplicate tests.
- [ ] **P07-T03 — Implement achievements.** Build hidden/visible achievements, progress, one-time unlock, cross-game/global grants, and backfill. Depends on P07-T02, P06-T06. Evidence: unlock/backfill tests.
- [ ] **P07-T04 — Implement modifiers and unlock registry.** Provide typed modifiers, stacking rules, scopes, duration hooks, unlock ownership, and deterministic evaluation. Depends on P07-T01. Evidence: stacking golden tests.
- [ ] **P07-T05 — Generate TypeScript and Python SDKs.** Generate API clients, auth hooks, action envelopes, errors, cursors, receipts, event types, retries, and idempotency helpers. Depends on P05-T06, P04-T07. Evidence: contract server tests.
- [ ] **P07-T06 — Generate C#, Kotlin, and Swift SDKs.** Deliver equivalent clients, secure token interfaces, offline journal primitives, WebSocket protocol base, and package publishing. Depends on P07-T05. Evidence: platform CI matrix.
- [ ] **P07-T07 — Build SDK conformance harness.** Run identical create/read/action/error/version/idempotency scenarios against every SDK. Depends on P07-T05–T06. Evidence: parity report.
- [ ] **P07-T08 — Document integration contract.** Publish generated reference, quickstart using synthetic fixtures, compatibility policy, retry policy, and release process. Depends on P07-T07. Evidence: documentation test.

## Exit gate

Progression, quests, achievements, modifiers, and unlocks pass domain tests. All five SDKs pass the same contract suite and are released to private registries.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 06 handoff, schema/runtime/data/API contracts, and repository compatibility rules.

### Exact outputs

Domain packages and persistence adapters for progression, quests, achievements, modifiers, and unlocks; event projectors; API schemas/routes; graph/quest test fixtures; SDK generators and outputs under `packages/sdk-{python,typescript,csharp,kotlin,swift}/`; private-registry release definitions; and `tests/contract/sdk-conformance/`.

At exit the progression API supports graph/status/read and action-based unlock/complete/claim; quest and achievement projections can rebuild from events; modifier ordering is stable by priority then ID; and global unlocks invoke approved cross-game delivery.

### SDK surface

Each SDK contains Supabase token-provider interface, typed REST client, idempotency helper, retry classifier, opaque cursors, ETags, action receipts, state patches, error codes, operation polling, offline journal primitives, event types, WebSocket protocol base, telemetry hooks, and version negotiation. SDKs never embed game definitions or authoritative rules.

Generate one language-neutral conformance scenario file. Run it unchanged through all SDKs against the same testing API. Verify serialization bytes, headers, errors, retry behavior, cursor handling, token refresh, idempotency, and unknown additive response fields. Publish immutable prerelease packages and verify installation in clean sample projects.

### Handoff to Phase 08

Provide progression/quest/achievement interfaces, event rebuild commands, modifier order contract, generated OpenAPI/schema digests, SDK package coordinates/digests, and compatibility-test command.
