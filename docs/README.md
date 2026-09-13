# LenGeas Documentation Map

Read these documents in order. Earlier documents define constraints consumed by later documents.

## Product and architecture

1. [Product charter](00-product-charter.md) — outcome, v1 boundary, exclusions, success metrics.
2. [Principles and invariants](01-principles-and-invariants.md) — rules that every component must preserve.
3. [System architecture](02-system-architecture.md) — runtime topology, ownership, trust, and request flows.
4. [Technology standard](03-technology-standard.md) — the selected stack; alternatives are not implementation choices.
5. [Repository and engineering standard](04-repository-and-engineering-standard.md) — monorepo, branches, reviews, IDs, time, numeric rules.

## Platform contracts

6. [Game Definition Schema v0.1](05-game-definition-schema-v0.1.md)
7. [Runtime and rules](06-runtime-and-rules.md)
8. [Data and persistence](07-data-and-persistence.md)
9. [Identity, tenancy, and authorization](08-identity-tenancy-authorization.md)
10. [API, events, jobs, and timers](09-api-events-jobs-timers.md)
11. [Versioning, publishing, LiveOps](10-versioning-publishing-liveops.md)
12. [Saves, offline play, and synchronization](11-saves-offline-sync.md)
13. [Simulation, balance, experiments, and analytics](12-simulation-balance-experiments-analytics.md)
14. [Game Studio](13-game-studio.md)
15. [Mechanics package contracts](14-mechanics-packages.md)
16. [Multiplayer](15-multiplayer.md)
17. [AI agent control plane](16-ai-agent-control-plane.md)

## Production readiness

18. [Security and abuse prevention](17-security-and-abuse-prevention.md)
19. [Observability, SRE, and disaster recovery](18-observability-sre-disaster-recovery.md)
20. [Testing and quality gates](19-testing-and-quality-gates.md)
21. [Infrastructure and deployment](20-infrastructure-and-deployment.md)
22. [Operations and governance](21-operations-and-governance.md)
23. [Platform completion contract](22-platform-completion-contract.md)
24. [Traceability matrix](23-traceability-matrix.md)
25. [Assets, localization, and notifications](24-assets-localization-notifications.md)

## Execution

- [Phase dependency map](phases/README.md)
- [Phase 00 through Phase 17](phases/README.md#phase-index)
- [ADR index](decisions/README.md)
- [Task record template](templates/task-record.md)
- [ADR template](templates/adr.md)
- [Phase-agent prompt template](templates/phase-agent-prompt.md)
- [Phase review template](templates/phase-review.md)

## Authority order

When two documents conflict, resolve the conflict in this order:

1. Accepted ADRs.
2. Product charter and platform invariants.
3. Platform contract documents.
4. Phase documents.
5. Task records and runbooks.

The conflict must still be removed from the lower-authority document before the affected phase closes.
