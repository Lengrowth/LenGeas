# Versioning, Publishing, and LiveOps

## Independent versions

- Engine: semantic version of evaluator behavior.
- Definition schema: semantic version of authoring contract.
- Definition: immutable monotonic game release version plus digest.
- Module: semantic version plus artifact digest.
- API: major version in URL and full OpenAPI artifact digest.
- Save schema: monotonic integer per game.
- Event: major version in event type.

A published definition locks exact engine range, schema digest, module versions, module digests, and localization digests.

## Publishing state machine

```text
draft -> testing -> staging -> published -> deprecated -> archived
  |         |          |
  +---------+----------+-> rejected
```

Transitions are API commands with authorization, idempotency, comment, validation report, actor, and audit record. Published content is immutable. Rollback changes a channel pointer to a previously published compatible version; it does not mutate a version.

## Pipeline

1. Freeze the draft and calculate canonical digest.
2. Validate schemas, references, graphs, semantics, safety rules, formulas, localization, and module compatibility.
3. Run unit and conformance tests against the resolved bundle.
4. Run save migration dry-runs from every supported production version.
5. Run mandatory simulations and balance assertions.
6. Produce a signed release report and resolved bundle in private R2.
7. Promote to staging and run smoke, API, SDK, and synthetic-player tests.
8. Hold a minimum 24-hour staging soak for normal releases; emergency security releases use the incident change process.
9. Collect game-owner and platform-release approvals.
10. Atomically update the production channel pointer.
11. Warm caches, monitor canaries, and expand assignment from 1% to 10%, 50%, and 100% when health gates pass.
12. Automatically roll back the channel pointer on integrity, error-rate, latency, or economy anomaly thresholds.

## Player pinning

Players are assigned a definition through an immutable release channel decision recorded in their game profile. A session pins the digest for its lifetime. Migration to a new definition occurs between sessions through an idempotent migration action. Active matches never change definition.

## Remote configuration

Remote configuration contains only fields marked `liveops_mutable` by schema. Allowed v1 fields are activation windows, presentation text keys, non-authoritative UI ordering, event enablement, reward multipliers within approved bounds, offer visibility, and declared tuning parameters within approved ranges.

Remote config cannot change identity, entitlements already granted, formula operators, action authority, security rules, ledger semantics, item ownership, match result rules, or schema structure. Each override has owner, reason, target cohort, start, end, bounds, approval, and automatic expiry.

## LiveOps objects

`LiveEvent`, `Season`, `Offer`, `QuestSchedule`, `ContentActivation`, and `RemoteOverride` are versioned objects. Time windows use UTC, include preflight overlap checks, and define end behavior. A kill switch exists for every live event and offer.

## Rollback and forward repair

- Definition rollback changes the active pointer only when the prior version accepts current saves.
- Incompatible state changes use a forward repair definition and migration.
- Granted value is never removed by a definition rollback. Compensation is a separate audited transaction.
- A failed publication preserves bundle, report, logs, and stage for investigation.

## Package publishing

Mechanics packages pass schema, contract, deterministic replay, migration, security, and performance suites. The internal registry stores signed manifests and artifacts. Definitions consume exact package digests. Revoked packages cannot enter new publications; existing affected releases trigger an incident decision.
