# Phase 08 — Registry, Publishing, and LiveOps

## Goal

Deliver immutable definition/module registries, environment promotion, safe rollout, rollback, remote configuration, and LiveOps.

## Entry

Phase 07 is accepted.

## Tasks

- [ ] **P08-T01 — Implement definition registry.** Store drafts, branches, immutable versions, bundle digests, R2 artifacts, channels, statuses, authors, and ancestry. Evidence: immutability tests.
- [ ] **P08-T02 — Implement module registry.** Store signed package manifests/artifacts, exact dependency resolution, compatibility, revocation, and install validation. Depends on P08-T01. Evidence: resolution suite.
- [ ] **P08-T03 — Implement publishing pipeline.** Orchestrate freeze, validation, tests, migration rehearsal, simulation hook, signed report, staging, soak, approvals, canary, and channel update. Depends on P08-T01–T02, P04-T05–T06. Evidence: full synthetic publish.
- [ ] **P08-T04 — Implement definition migration/pinning.** Pin sessions, migrate players between sessions, enforce compatibility, report migration status, and stop incompatible rollback. Depends on P08-T03, P07-T01. Evidence: mixed-version tests.
- [ ] **P08-T05 — Implement rollback.** Move channel pointers, monitor canary gates, warm caches, preserve granted value, and forward-repair incompatible state. Depends on P08-T03–T04. Evidence: rollback/re-promotion drill.
- [ ] **P08-T06 — Implement remote config.** Enforce mutable-field allowlists, numeric bounds, cohorts, approvals, UTC windows, expiry, kill switch, and audit. Depends on P08-T03. Evidence: prohibited-field tests.
- [ ] **P08-T07 — Implement LiveOps.** Deliver events, seasons, quest schedules, content activation, offers, calendars, closure behavior, and overlapping-schedule validation. Depends on P08-T06, P07-T02. Evidence: time-travel suite.
- [ ] **P08-T08 — Secure publishing.** Enforce separation of duties, signed artifacts, provenance, environment permissions, AI prohibition, and complete audit reconstruction. Depends on P08-T03–T07. Evidence: authorization/red-team report.
- [ ] **P08-T09 — Build assets and localization.** Implement asset metadata/lifecycle, R2 quarantine/approved storage, Queue-to-Celery scanning, ClamAV and image sanitization, Cloudflare Images variants, signed delivery, licenses/takedown, ICU MessageFormat catalogs, fallback, schema validation, and definition reference checks. Depends on P08-T01, P02-T06. Evidence: malicious-upload, CDN-revocation, and locale conformance reports.

## Exit gate

A synthetic definition and module pass full promotion, canary, rollback, migration, remote override, LiveOps activation, and audit reconstruction without changing an application image.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 07 handoff and the schema, persistence, publishing, API/job, security, and SRE contracts.

### Exact outputs

Definition/module registry domains and repositories; R2 bundle adapter; publishing Celery workflow; validation/migration/simulation stage adapters; channel assignment service; LiveOps/remote-config domains; API routes/schemas; signing/provenance; audit projectors; `docs/runbooks/{definition-publish,definition-rollback,bad-definition,module-revocation,liveops-kill-switch}.md`; and tests under `tests/{contract,integration,e2e,security}/publishing/`.

P08-T09 additionally creates `packages/domain/{assets,localization}/`, asset/localization API schemas/routes, MongoDB metadata repositories, R2/Images/Queue adapters, `apps/workers/asset-worker/`, Studio-ready view models, and upload/scan/license/takedown/localization runbooks and tests.

### Required state machines and APIs

Implement draft/testing/staging/published/deprecated/archived/rejected transitions with expected version. Expose draft CRUD/patch/freeze/validate, version read/diff, stage/promote/approve/publish/rollback, channel read, module release/install/revoke, remote override CRUD/kill, and LiveOps schedule APIs. Every command has idempotency, actor, reason, environment, and audit record.

The publish workflow persists one operation resource with stage attempts and artifact digests. It resumes after worker failure without rerunning successful content-addressed stages. Approval is two-person and author/AI separation is enforced. Canary health reads named error/latency/integrity/economy metrics and automatically re-points the channel on breach.

### Required scenarios

Race two publishers, mutate a frozen draft, corrupt an R2 bundle, revoke a module, fail every workflow stage, expire approval, attempt self/AI approval, migrate mixed player versions, rollback across incompatible save state, activate overlapping events, exceed remote bounds, and reconstruct every prior/new value from audit.

### Handoff to Phase 09

Provide active-definition resolver, channel/pinning interface, bundle/signature contract, migration hook, operation API, remote-config resolver, LiveOps timer needs, asset/localization APIs, audit event list, and rollback/takedown runbooks.
