# Phase 00 — Charter and Architecture Lock

## Goal

Ratify one implementable v1 boundary and eliminate unresolved foundational choices before code begins.

## Entry

The documentation set exists and the sole developer/repository owner is the accountable product, technical, architecture, security, operations, and release owner for this one-person company.

Approval model: the repository owner makes every Phase 00 decision. Role IDs remain internal responsibility labels only; no separate reviewers, approval panel, meeting, signature, or external governance process is required.

## Tasks

- [x] **P00-T01 — Approve product charter.** The repository owner approves v1 scope, exclusions, metrics, and the no-game rule in `00-product-charter.md`. Evidence: owner decision record.
- [x] **P00-T02 — Approve platform invariants.** The repository owner approves every invariant in `01-principles-and-invariants.md` under the internal role labels. Evidence: owner decision record.
- [x] **P00-T03 — Review architecture.** The repository owner validates Cloudflare/AWS ownership, primary/DR regions, service boundaries, trust boundaries, failure modes, and data flows. Evidence: architecture decision record and threat-diagram digest.
- [x] **P00-T04 — Accept technology ADRs.** The repository owner accepts ADRs for the stack, Cloudflare/AWS split, MongoDB Atlas, ECS on EC2, RabbitMQ/Celery, MSK, OpenNext, and Terraform. Evidence: accepted ADR links.
- [x] **P00-T05 — Assign ownership.** The repository owner owns every domain, service, package, schema, phase, SLO, and vendor; backups are same-owner fallback labels. Evidence: ownership matrix.
- [x] **P00-T06 — Baseline requirements.** Every mandatory statement has an `RQ-` mapping and every requirement has a phase and evidence path. Evidence: traceability audit.
- [x] **P00-T07 — Establish risk register.** The repository owner records top architectural, vendor, cost, security, performance, and staffing risks with owner, trigger, mitigation, and review date. Evidence: approved register.
- [x] **P00-T08 — Approve completion contract.** The repository owner approves `22-platform-completion-contract.md` and the Phase 00 evidence. Evidence: owner decision record.

## Exit gate

All tasks are accepted by the repository owner, there is no open decision labeled TBD, the traceability audit has no orphan requirements, and the repository owner records `Phase 00 PASS`. Product code remains absent.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). This phase changes documentation and governance records only.

### Required reading

`docs/00-product-charter.md`, `01-principles-and-invariants.md`, `02-system-architecture.md`, `03-technology-standard.md`, `17-security-and-abuse-prevention.md`, `20-infrastructure-and-deployment.md`, `22-platform-completion-contract.md`, and `23-traceability-matrix.md`.

### Exact outputs

| Task | Required files |
|---|---|
| P00-T01 | `docs/governance/product-charter-approval.md`, `scope-register.yaml` |
| P00-T02 | `docs/governance/invariant-review.md`, `requirement-register.yaml` |
| P00-T03 | `docs/architecture/{context,container,deployment,data-flows,trust-boundaries}.md` and diagrams under `docs/architecture/diagrams/` |
| P00-T04 | ADR files `docs/decisions/0001` through `0010` listed in the ADR index |
| P00-T05 | `CODEOWNERS`, `docs/governance/ownership.yaml`, `on-call-roles.md` |
| P00-T06 | `docs/governance/requirements.yaml` and generated traceability matrix |
| P00-T07 | `docs/governance/{risk-register,vendor-register}.yaml` |
| P00-T08 | Complete `docs/evidence/phase-00/` tree |

Every YAML record has a JSON Schema under `docs/governance/schemas/`. Extract every v1 bullet and every `MUST` into the requirement register with source anchor, owner, phase task, verification method, and evidence path. Produce C4 diagrams plus action, publish, sync, purchase, event, async match, realtime match, and AI-review sequence diagrams. Scan for duplicate IDs, broken links, unowned components, orphan requirements/tasks, and TBD/TODO/FIXME. Store reports under `docs/evidence/phase-00/`.

### Handoff to Phase 01

`handoff.md` lists accepted ADR digests, exact tool versions to pin, repository topology, required root commands, CI gates, owner mappings, and requirement-register digest. The repository owner may change them only through a documented superseding ADR. Phase 01 must not begin until this owner approval is recorded.
