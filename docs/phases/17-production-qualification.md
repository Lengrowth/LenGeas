# Phase 17 — Production Qualification and Completion

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). This phase adds hardening, tests, runbooks, and fixes only; it cannot defer a failed v1 requirement.

## Mission

Prove the entire v1 platform in production topology, close every mandatory finding, and produce the signed completion record that alone permits first-game planning.

## Required reading and entry

Phases 00–16 must be `accepted` with validated manifests and no mandatory follow-up. Read every handoff, `17-security-and-abuse-prevention.md` through `23-traceability-matrix.md`, every operational runbook, and all accepted ADRs.

## Tasks

- [ ] **P17-T01 — Security qualification.** Update data-flow/threat models, run SAST/DAST/fuzz/IaC/container/dependency/secret/authorization/tenant/formula/upload/multiplayer/agent abuse suites, commission independent penetration test, and close every critical/high finding. Outputs: `security/qualification.md`, pentest digest, remediation evidence.
- [ ] **P17-T02 — Supply-chain qualification.** Verify every lock, image digest, SBOM, provenance, Sigstore signature, ECR/Worker deployment rule, OIDC trust, secret inventory/rotation, dependency license, and vulnerable artifact block. Outputs: signed artifact inventory and tamper drill.
- [ ] **P17-T03 — Performance/capacity qualification.** Test API, Studio, publish, migration, event, task, timer, simulation, analytics, sync, WebSocket, and match targets at expected peak plus 30% headroom. Validate autoscaling, quotas, telemetry cardinality, and per-tenant cost. Outputs: raw specs/results and capacity plan.
- [ ] **P17-T04 — Determinism/integrity qualification.** Run one billion simulated actions, 1,000 seeds per handler, forced duplicate command/task/event/webhook/timer/result, all save/package migrations, ledger reconciliation, purchases/refunds, cross-game grants, async/realtime replays, and state digests across ARM64/x86. Any unexplained difference fails.
- [ ] **P17-T05 — Dependency and AZ chaos.** Kill ECS tasks/instances, block Atlas/Valkey/RabbitMQ/MSK/R2/Supabase/Resend, fill queues, expire leases, fail one AZ, deploy a bad Worker/API/definition/module, and verify defined degradation, alerts, rollback, replay, and no duplicated value.
- [ ] **P17-T06 — Backup and regional DR.** Restore Atlas point-in-time and R2 versions, recover Terraform state, rebuild Valkey, replay outbox/MSK, provision `eu-west-1`, shift edge, verify data/integrity/SLO, and fail back. Measured RPO must be at most 15 minutes and RTO at most 4 hours.
- [ ] **P17-T07 — Operational qualification.** Exercise every Sev-1 runbook and pager, support case/compensation, privacy export/deletion, access recertification, key rotation, bad release, cost alert, vendor outage, security incident, communication, and postmortem process with named on-call owners.
- [ ] **P17-T08 — Thirty-day soak.** Operate multiple synthetic studios/games with every package and required combination, offline devices, LiveOps schedules, experiments, monetization sandbox, simulations, AI proposals, async/realtime matches, continuous reconciliation/data quality, deploys, rotations, and canaries. Pass monthly SLOs.
- [ ] **P17-T09 — No-orphan audit.** Enumerate requirements, tasks, evidence, owners/backups, code packages, services, routes, collections/indexes, events, tasks, timers, schemas, definitions, modules, SDKs, resources, dashboards, alerts, runbooks, retention rules, secrets, vendors, and costs. Every item maps bidirectionally and Terraform has zero unexplained drift.
- [ ] **P17-T10 — Completion review.** Execute the 12 mandatory demonstrations in `22-platform-completion-contract.md`. Product, Architecture, Security, SRE, Data, Game Systems, Multiplayer, Studio, and QA independently sign the release tag and evidence digests. Publish `docs/evidence/platform-v1-completion.md` with `Platform Completion Review: PASS` only if every threshold passes.
- [ ] **P17-T11 — First-game planning unlock.** After P17-T10, create a separate discovery charter and requirements document. Do not create game code, assets, content definitions, or renderer in this phase.

## Exact final evidence

`docs/evidence/phase-17/` contains raw and summarized security, supply-chain, performance, integrity, chaos, DR, operations, soak, and traceability reports; command logs; artifact/resource inventory; cost baseline; all reviewer signatures; and SHA-256 manifest. Large raw results live in private R2 and are referenced by immutable digest and signed URL policy.

## Exit gate

LenGeas is totally ready within the v1 boundary only when P17-T10 records `PASS`. A waiver, accepted risk, partial demo, design argument, or future task cannot satisfy a failed mandatory threshold. Before `PASS`, first-party game implementation remains forbidden.
