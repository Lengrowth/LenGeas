# Traceability Matrix

This matrix maps product requirements to authoritative design documents, delivery phases, and final evidence. Detailed task dependencies are in the phase documents.

| Requirement | Contract | Phase(s) | Final evidence |
|---|---|---|---|
| RQ-001 Systems/mechanics/content separation | 00, 01, 05, 14 | 00, 04, 12, 13 | Blueprint isolation suite |
| RQ-002 Data-driven definitions | 05, 10 | 04, 08 | Schema and publish reports |
| RQ-003 Deterministic universal runtime | 01, 06 | 05 | Cross-platform replay report |
| RQ-004 Economy transaction integrity | 06, 07 | 06 | Billion-action reconciliation |
| RQ-005 Progression, quests, achievements | 05, 06 | 07 | Graph and event conformance |
| RQ-006 Universal identity and guests | 08 | 03 | Identity/merge E2E report |
| RQ-007 Tenant/game isolation | 01, 07, 08, 17 | 03, 17 | Tenant escape report |
| RQ-008 Saves, migrations, offline sync | 11 | 09 | Multi-device conflict report |
| RQ-009 Immutable versioning/publishing | 10 | 08 | Rollback and re-promotion report |
| RQ-010 Events/jobs/timers | 09 | 05, 10 | Duplicate-delivery and backlog report |
| RQ-011 Simulation and balance | 12 | 10 | Deterministic simulation report |
| RQ-012 Experiments and analytics | 12 | 10, 11 | SRM/data-quality/decision report |
| RQ-013 LiveOps/monetization/entitlements | 10, 17 | 11 | Purchase and kill-switch report |
| RQ-014 Game Studio | 13 | 12 | Author-to-publish E2E report |
| RQ-015 Solo mechanics packages | 14 | 13 | Package release reports |
| RQ-016 Social/async multiplayer | 15 | 14 | Async lifecycle/load report |
| RQ-017 Real-time multiplayer | 15 | 15 | WebSocket/match load report |
| RQ-018 AI agent platform | 16 | 16 | Scope red-team and proposal report |
| RQ-019 AWS/Cloudflare production infrastructure | 02, 03, 20 | 02, 17 | Terraform reproduction report |
| RQ-020 Security/privacy/abuse | 17 | 03, 06, 09, 11, 15, 16, 17 | Penetration and privacy reports |
| RQ-021 Observability/SRE/DR | 18 | 02, 10, 14, 15, 17 | SLO, alert, restore, DR reports |
| RQ-022 Multi-language SDKs | 04, 09 | 07, 14, 15 | SDK conformance report |
| RQ-023 Human/AI shared interfaces | 13, 16 | 12, 16 | Identical API audit |
| RQ-024 Platform completion before first game | 00, 22 | 00, 17 | Signed completion record |
| RQ-025 Assets, localization, notifications | 24 | 08, 10, 12 | Upload-to-delivery, locale, and provider-failover evidence |

## Maintenance rule

A new mandatory requirement receives the next `RQ-` ID, an authoritative contract, phase tasks, test evidence, and an updated completion review. A deleted requirement requires a charter-changing ADR.

## Phase 00 generated audit

The Phase 00 generated register and audit view are [requirements.yaml](governance/requirements.yaml) and [traceability-matrix.generated.md](governance/traceability-matrix.generated.md). They preserve the 25 baseline IDs in this matrix and attach Phase 00 evidence without changing the authoritative requirement statements.

## Phase 00 generated baseline

The machine-readable baseline is [docs/governance/requirements.yaml](governance/requirements.yaml), generated from [docs/governance/requirement-register.yaml](governance/requirement-register.yaml). The Phase 00 audit records source anchors, owner roles, verification methods, and evidence paths for all 25 matrix requirements. Human acceptance remains required.
