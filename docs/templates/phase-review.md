# Phase <XX> Review

- Phase document:
- Candidate commit/tag:
- Manifest digest:
- Reviewer roles:
- Review UTC:

## Prerequisites

- [ ] Prior phase is accepted.
- [ ] Required reading and ADRs exist at recorded digests.
- [ ] Every task is `in_review` with valid evidence.
- [ ] Requirement/task/artifact/evidence links have no orphan.

## Independent verification

- [ ] Clean-clone bootstrap passes.
- [ ] `task verify` passes.
- [ ] `task phase:gate PHASE=<XX>` passes.
- [ ] Security/privacy negative cases pass.
- [ ] Rollback/failure scenario passes.
- [ ] Documentation, OpenAPI/schemas, generated outputs, dashboards, alerts, and runbooks match behavior.
- [ ] No TODO/FIXME/placeholder/mandatory skip exists.
- [ ] No first-party game or out-of-phase feature exists.

## Findings

List finding ID, severity, owner, evidence, and resolution. Critical/high or mandatory findings block acceptance.

## Decision

`accepted | changes_required`

Record each reviewer name, role, signature, UTC, and the final evidence digest. Acceptance authorizes only the next documented phase.
