# Phase 05 — Runtime Primitives

## Goal

Deliver the deterministic headless evaluator and minimal action API without genre mechanics.

## Entry

Phase 04 is accepted.

## Tasks

- [ ] **P05-T01 — Build execution context.** Implement pinned engine/definition/packages, logical time, seed, experiment context, locale, actor, namespaces, and budgets. Evidence: context immutability tests.
- [ ] **P05-T02 — Build state-path registry.** Resolve typed paths, read/write permissions, missing-value behavior, and package ownership at publication. Depends on P05-T01. Evidence: namespace escape tests.
- [ ] **P05-T03 — Build condition/formula evaluators.** Implement every AST operator, explanation trees, decimal rules, overflow handling, complexity limits, and property tests. Depends on P05-T01–T02. Evidence: evaluator conformance.
- [ ] **P05-T04 — Build action planner.** Validate input, conditions, costs, effects, rewards, timers, events, ordering, and operation budgets into an immutable plan. Depends on P05-T03. Evidence: plan golden tests.
- [ ] **P05-T05 — Build effect/reward registries.** Implement core handlers, expansion, namespace enforcement, and package registration freeze. Depends on P05-T02, P05-T04. Evidence: handler contract report.
- [ ] **P05-T06 — Build minimal action API.** Create game, create draft definition, validate definition, create player, execute action, and read receipt/state endpoints with authorization and idempotency boundaries. Depends on P03-T05, P05-T04–T05. Evidence: API E2E.
- [ ] **P05-T07 — Build event/outbox primitives.** Produce envelopes, causation, correlation, transactional outbox records, and consumer inbox contracts without full broker operations. Depends on P05-T04. Evidence: duplicate envelope tests.
- [ ] **P05-T08 — Prove determinism and performance.** Replay generated actions and 1,000 seeds on local/CI ARM64 and x86-64 within runtime budgets. Depends on P05-T01–T07. Evidence: signed replay report.

## Exit gate

The minimal API executes definition-driven actions and returns identical receipts/state digests across supported architectures. No genre package or direct state mutation exists.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 04 handoff, ADR 0007, and the principles, schema, runtime, API/event, and test contracts.

### Exact outputs

`packages/runtime/src/lengeas_runtime/{context,state_paths,conditions,formulas,actions,effects,rewards,events,timers,registry,serialization,errors}/`; `packages/domain/actions/`; API v1 game/definition/player/action routers; MongoDB player-state/action-receipt/idempotency/outbox adapters; runtime tests in unit/property/contract/integration/determinism; conformance fixtures; and generated runtime reference.

The runtime package dependency test forbids FastAPI, PyMongo, Valkey, Celery, Kafka, R2, filesystem, environment, network, system clock, and unseeded RNG imports.

### Interfaces and failure tests

The evaluator accepts immutable state plus the execution tuple and returns `Allowed(plan)` or `Denied(explanation)`. It never mutates input. P05-T06 must expose create game, create draft definition, validate definition, create player, execute action, read receipt, read state, health, and version endpoints. P05-T07 commits state, receipt, idempotency record, and outbox in one transaction.

Property tests cover Boolean laws, numeric boundaries, formula limits, effect order, reward expansion, namespace access, canonical serialization, seeds, and operation budgets. Integration tests kill execution before/after commit, inject transient Mongo errors, repeat an idempotency key with equal/different payloads, race expected versions, and verify committed/denied/conflict/unknown receipts.

Run runtime unit/property tests, API contract tests, action-transaction integration, dependency-boundary scan, ARM64/x86 deterministic replay over 1,000 seeds, performance budgets, and `task phase:gate PHASE=05`.

### Handoff to Phase 06

Provide evaluator API, registration protocol, transaction extension points, receipt/outbox schemas, runtime benchmark, RNG algorithm version, and minimal fixture action stream.
