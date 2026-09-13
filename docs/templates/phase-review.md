# Phase <XX> Review

- Phase document:
- Candidate commit/tag:
- Manifest digest:
- Reviewer: repository owner or designated review agent
- Review UTC:

## Prerequisites

- [ ] Prior phase is accepted.
- [ ] Required reading and ADRs exist at recorded digests.
- [ ] Every task is `in_review` with valid evidence.
- [ ] Requirement/task/artifact/evidence links have no orphan.

## Verification

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

Record the reviewer identity, UTC, final evidence digest, and recommendation. A review agent returns `ready_for_owner_approval` or `changes_required`; it does not accept the phase. The repository owner records `accepted` without a second reviewer or signature. Acceptance authorizes only the next documented phase.
