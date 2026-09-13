# Phase 09 — Saves and Offline Sync

## Goal

Deliver versioned saves, deterministic migrations, offline journals, multi-device reconciliation, and fraud quarantine for every network mode.

## Entry

Phase 08 is accepted.

## Tasks

- [ ] **P09-T01 — Implement save checkpoints.** Create canonical envelope, immutable checkpoints, current pointers, compression, encryption, digests, retention, and restore. Evidence: round-trip/golden tests.
- [ ] **P09-T02 — Implement save migrations.** Register pure step migrations, chain resolution, dry-run, idempotency, rollback constraints, telemetry, and golden fixtures. Depends on P09-T01, P08-T04. Evidence: every-version matrix.
- [ ] **P09-T03 — Implement client journal contract.** Define device keys, sequences, action/result digests, logical time, seeds, compression, secure local storage interface, and SDK support. Depends on P07-T06, P09-T01. Evidence: cross-SDK journal parity.
- [ ] **P09-T04 — Implement replay sync.** Validate checkpoint/journal, replay on server runtime, compare digests, commit accepted actions, and return patch/rebase. Depends on P09-T02–T03, P05-T08. Evidence: deterministic sync suite.
- [ ] **P09-T05 — Implement domain conflict resolution.** Apply action replay for value domains, preference latest-valid update, branch selection, non-commutative rejection, and multi-device order. Depends on P09-T04. Evidence: conflict matrix.
- [ ] **P09-T06 — Implement offline progress.** Aggregate generators/timers, enforce 30-day platform cap, detect clock shifts, issue calculation receipts, and prove aggregate/tick equivalence. Depends on P09-T04. Evidence: time/rounding property suite.
- [ ] **P09-T07 — Implement quarantine and support.** Detect impossible rate, invalid signature, definition mismatch, divergence, device fan-out; quarantine disputed value and expose audited resolution. Depends on P09-T04–T06. Evidence: fraud injection tests.
- [ ] **P09-T08 — Load and chaos test sync.** Run 10,000 concurrent divergent syncs, duplicate/resume/network-loss cases, and Atlas/Valkey failovers. Depends on P09-T01–T07. Evidence: load/chaos report.

## Exit gate

All network modes pass; two-device divergent journals resolve deterministically; economy duplication is zero; save migrations cover every supported version; quarantine and recovery are operable.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 08 handoff and the runtime, persistence, publishing, save/sync, security, and SDK contracts.

### Exact outputs

Save/checkpoint/migration/sync domains; MongoDB repositories and R2 export adapter; API schemas/routes for checkpoint, sync preview/commit, conflict choice, quarantine, and recovery; SDK journal implementations in all client SDKs; migration registry/CLI; fraud signal rules; support runbooks; and `tests/conformance/fixtures/saves/v*/`.

### Protocol requirements

The sync request contains checkpoint, state/definition/engine digests, device ID, monotonically increasing sequence, signed compressed journal, and client diagnostics. The response contains accepted sequence, canonical patch/snapshot, new checkpoint, rejected action codes, migration requirements, quarantine/support reference, and server time. Preview has no mutation; commit uses a sync idempotency key.

Migrations are adjacent-version pure functions with golden before/after/digest fixtures. The agent must build a matrix from every supported version to current and validate rerun behavior. Offline aggregation must equal bounded tick execution under declared rounding. Economy/inventory/entitlement conflicts always replay transactions; no winner snapshot applies.

### Required tests

Two devices, out-of-order/repeated/missing journal sequence, stolen key, altered snapshot, altered result digest, stale definition, clock rollback/forward, 30-day cap, concurrent commit, network loss at commit, migration failure, branch choice, non-commutative action, Atlas failover, Valkey lease loss, and 10,000 concurrent divergent syncs.

### Handoff to Phase 10

Provide checkpoint/journal/sync schemas, migration registry, device verification interface, timer offline-catch-up interface, fraud signals, quarantine workflow, SDK journal status, and sync performance baseline.
