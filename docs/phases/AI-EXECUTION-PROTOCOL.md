# AI Phase Execution Protocol

This protocol is binding for every AI agent implementing a LenGeas phase.

## Invocation contract

The orchestrator gives the agent exactly one phase document and repository access. The agent must read, in this order:

1. `README.md`.
2. `docs/00-product-charter.md` through `docs/04-repository-and-engineering-standard.md`.
3. Every contract document named by the phase under **Required reading**.
4. Every accepted ADR named by the phase.
5. `docs/evidence/phase-<previous>/handoff.md` and `manifest.json`.
6. The assigned phase document.

The agent must stop before implementation if a required file is missing, a prerequisite phase is not `accepted`, or two authoritative documents conflict. It records the block in `docs/evidence/phase-XX/blockers.md`; it does not choose a new architecture.

## Work loop

For every task ID, the agent performs this exact loop:

1. Confirm dependencies have accepted evidence.
2. Inspect current repository state and preserve unrelated work.
3. Create or update only the paths listed in the task's artifact manifest.
4. Implement the smallest complete vertical slice described by the task.
5. Add unit, property, contract, integration, security, and operational tests named by the task.
6. Run the task's validation commands.
7. Record command, exit code, tool versions, commit SHA, artifact digests, and result under `docs/evidence/phase-XX/tasks/<task-id>.md`.
8. Update traceability for every implemented requirement.
9. Commit using `<task-id>: <imperative summary>` only after validation passes.

An agent cannot mark its own phase `accepted`. It marks tasks `in_review`; the repository owner records acceptance. In a one-person company, the repository owner may hold every role and approve directly without a separate reviewer, meeting, or signature process.

## Required evidence tree

```text
docs/evidence/phase-XX/
  manifest.json
  handoff.md
  blockers.md
  decisions.md
  commands.ndjson
  test-report.xml
  coverage.json
  security/
  performance/
  operations/
  tasks/
    PXX-T01.md
```

`manifest.json` contains phase, status, start/end UTC, base/final commit, agent identity, toolchain versions, completed task IDs, requirement IDs, artifacts with SHA-256, tests, open risks, and next-phase prerequisites. Its schema lives at `packages/schemas/evidence/phase-manifest.schema.json` after Phase 01.

## Deterministic repository commands

Phase 01 creates these commands in the root `Taskfile.yml`; later agents use them without inventing replacements:

- `task bootstrap` — install pinned toolchains and dependencies.
- `task generate` — regenerate schemas, models, clients, docs, and protocol bindings.
- `task format` — apply deterministic formatters.
- `task lint` — lint code, schemas, Terraform, Dockerfiles, Markdown, and links.
- `task typecheck` — strict Python and TypeScript checks plus generated SDK compilation.
- `task test:unit`, `task test:property`, `task test:contract`, `task test:integration`, `task test:e2e`.
- `task test:security`, `task test:performance`, `task test:determinism`, `task test:dr`.
- `task verify` — all merge-gate checks.
- `task evidence PHASE=XX` — validate and hash phase evidence.
- `task phase:gate PHASE=XX` — run the phase-specific gate without accepting it.

Every command must work on Windows PowerShell and Linux. Commands cannot require a developer to click a cloud console.

## Change boundaries

The agent must not:

- start later-phase product features;
- create a first-party game or renderer;
- change a technology choice without an accepted ADR;
- weaken a test, budget, SLO, security control, or completion threshold to obtain a pass;
- write directly to production or use production player data;
- store credentials in files, logs, evidence, fixtures, or generated output;
- leave TODO, FIXME, placeholder handler, mocked production integration, skipped mandatory test, or undocumented manual step at phase exit;
- claim success from a partial command or a test that did not exercise the declared integration.

## Documentation updates

Each task updates the public contract when behavior changes, generated reference when a contract changes, runbook when failure behavior changes, ADR when architecture changes, and traceability row when evidence changes. Documentation is part of the task, never a cleanup phase.

## Handoff contract

`handoff.md` states exactly:

- what is operational;
- public interfaces and version/digest;
- migrations applied and rollback boundary;
- feature flags and their required state;
- dashboards, alerts, and runbooks;
- known medium/low risks with owners;
- credentials or external setup the next phase needs, referenced by secret name only;
- exact first command for the next phase;
- prohibited assumptions.

The next phase cannot begin until the handoff and manifest validate and the current exit reviewer signs `accepted`.
