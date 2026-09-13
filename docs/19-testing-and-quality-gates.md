# Testing and Quality Gates

## Test pyramid

- Unit: pure conditions, formulas, actions, effects, rewards, timers, policies, migrations, and mechanics handlers.
- Property: resource conservation, non-negative constraints, idempotency, graph invariants, deterministic replay, serialization, and formula bounds.
- Contract: OpenAPI, JSON Schema, events, packages, SDKs, broker messages, and provider webhooks.
- Domain: economy, inventory, progression, quests, achievements, entitlements, saves, experiments, publishing, and matches.
- Integration: MongoDB, Valkey, RabbitMQ, MSK, R2, Supabase, Resend, ECS, and Cloudflare adapters.
- End-to-end: Studio authoring through production-like publish, client action, analytics, support, rollback, and restore.
- Performance: API, simulation, publishing, event, timer, sync, WebSocket, and match workloads.
- Security: authorization, fuzzing, abuse, supply chain, IaC, penetration, and incident drills.

## Determinism suite

Every runtime and package release replays golden streams across supported Python/OS architectures, 1,000 generated seeds per handler, serialized save migrations, and production-sampled redacted action shapes. State digest, ledger plan, event payloads, timer plan, and receipt payload must match exactly.

## Definition quality

Validation tests cover duplicate/missing references, cycles, reachability, impossible conditions, invalid formulas, negative/overflow rewards, deleted content, localization gaps, illegal authority, undeclared state paths, incompatible modules, remote-config bounds, and operation budgets.

## Economy exploit suite

Graph search detects profitable exchange cycles, repeated claims, concurrent purchase races, cancellation duplication, overflow routing loops, prestige retention leaks, offline replay duplication, refund re-grants, and cross-game reward loops. A ledger reconciliation run follows every scenario.

## Environments

Unit tests use in-memory pure models. Integration tests use Docker Compose with real version-pinned dependencies. Cloud integration tests use the testing environment. Staging carries production topology and synthetic data. Production verification is read-only or uses dedicated synthetic tenants.

## Merge gate

Every pull request must pass formatting, lint, strict types, unit/property tests, changed contract tests, schema compatibility, migration checks, dependency and secret scans, IaC validation, documentation links, and coverage threshold. Core runtime statement/branch coverage minimum is 95%; other backend and Studio code minimum is 85%.

## Release gate

Every release must pass full tests, deterministic replay, integration/end-to-end, migration rehearsal, performance regression, container/IaC/security scans, SBOM/provenance, staging smoke, and required soak. Schema, runtime, mechanics, infrastructure, and security releases require domain approval.

## Platform v1 qualification

Qualification includes:

- 30-day synthetic multi-game soak with all v1 packages enabled across separate blueprints;
- 1 billion simulated actions with zero unreconciled ledger entries;
- forced duplicate delivery for every command, task, event, webhook, timer, and match result;
- 100,000 concurrent WebSockets and 10,000 simultaneous matches;
- 10,000 concurrent offline sync submissions with divergent device journals;
- one-AZ failure and full regional DR exercise;
- backup restore and definition rollback exercises;
- tenant escape, role escalation, origin bypass, and AI tool-scope red teams;
- independent penetration test with all critical/high findings closed;
- SDK conformance on TypeScript, C#, Kotlin, Swift, and Python.

## Flaky test policy

A flaky test is a release defect. CI quarantining requires an owner, issue, diagnostic evidence, and seven-day deadline. Mandatory integrity, security, migration, and determinism tests cannot be quarantined.
