# Phase 05 handoff

## Status and decision

Phase 05 is `accepted`. On 2026-10-12 the repository owner explicitly accepted P05-T01 through P05-T08 and directed work to proceed to Phase 06, with the open evidence gaps in `blockers.md` disclosed. This acceptance does not claim unavailable external checks were completed. Phase 04 was `accepted` before this work began; its entry gate and read-only evidence verification passed. Phase 04's status is unchanged.

The Phase 05 source candidate is commit `186431fc3444d00f89df206a7ad1fc53448307af` (`P05-T01: implement Phase 05 runtime primitives`). The evidence update is committed separately after the final gates.

## Delivered interfaces

- Pure runtime package: `packages/runtime/src/lengeas_runtime/`.
- Typed path permissions and package ownership: `StatePathRegistry`.
- Conditions/formulas: bounded Decimal AST evaluators with immutable explanations.
- Action planning: `plan_action` returns immutable plans for costs, effects, rewards, timers, and events.
- Extensions: frozen `HandlerRegistry` with core schema effect/reward names.
- API surface: `/health`, `/version`, game creation, definition draft/validation, player creation, action execution, receipt reads, and state reads in `apps/api/app/runtime_api.py`.
- Atomic boundaries: in-memory contract adapter in `packages/domain/actions.py`; Mongo transaction adapter in `packages/persistence/mongodb/actions.py`; inbox adapter in `packages/persistence/mongodb/event_inbox.py`.
- Generated reference: `docs/reference/runtime-v1.md`.

## Validation results

- Runtime unit, property, contract, in-memory integration, local API E2E, security, performance, and determinism task selectors passed; combined report: 71 passed.
- Runtime statement coverage is 97.8%; branch coverage is 95.9% on the local focused run.
- `task generate`, `task format`, `task lint`, and `task typecheck` passed.
- Local 1,000-seed AMD64 replay passed and local 1,000-evaluation benchmark passed its declared budget.
- The full Mongo integration task and deployed E2E task failed closed because their external prerequisites are unavailable. The hosted ARM64/x86-64 workflow is configured but has not run.
- Local replay report is unsigned; no owner-managed signing key is configured.

Exact commands, exit codes, and results are in `commands.ndjson`; detailed test and coverage output is in `test-report.xml` and `coverage.json`.

## Risks and prerequisites

See `blockers.md` and the manifest `open_risks` for the MongoDB transaction, deployed E2E, hosted ARM64/x86-64 replay, signing, and benchmark-threshold gaps accepted by the repository owner. These are disclosed limitations, not claims of completed verification.

Phase 06 can consume the plan and registration contracts. It must supply domain handlers for economy/inventory grants and should retain the transaction boundary that commits state, receipt, idempotency, and outbox together.

## Exact first command for Phase 06

`task phase:gate PHASE=05`
