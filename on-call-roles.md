# On-call Roles

## Assignment status

The operational roles and same-person fallbacks are defined below. The current company is one developer: the repository owner. That developer covers every listed role and makes every operational decision. Paging configuration is deployment setup, not a Phase 00 approval gate.

| Role ID | Primary responsibility | Backup role | Paging scope | Assignment state |
|---|---|---|---|---|
| `platform_technical_lead` | Architecture, phase gates, high-risk change decisions | `architecture_owner` | Platform-wide | Sole developer owns and decides |
| `incident_commander` | Incident command, containment, communications, recovery approval | `sre_owner` | Sev-1 incidents | Sole developer owns and decides |
| `sre_owner` | SLOs, capacity, observability, DR, runbooks | `platform_operations_owner` | Availability and recovery | Sole developer owns and decides |
| `security_owner` | Security incidents, abuse, privacy, key rotation | `platform_technical_lead` | Security and privacy | Sole developer owns and decides |
| `data_owner` | Atlas, persistence, ledger integrity, retention, restore | `sre_owner` | Data and integrity | Sole developer owns and decides |
| `identity_owner` | Auth, identity, tenancy, authorization, guest merge | `security_owner` | Identity and access | Sole developer owns and decides |
| `multiplayer_owner` | Match, realtime, async, ratings, presence | `sre_owner` | Multiplayer | Sole developer owns and decides |
| `release_manager` | Release records, canaries, rollback, approvals | `qa_owner` | Release pipeline | Sole developer owns and decides |
| `qa_owner` | Quality gates, evidence, conformance, traceability | `release_manager` | Qualification | Sole developer owns and decides |

## Escalation rule

The sole developer acknowledges a page, records the incident or change ID, and uses the listed fallback role as a checklist rather than a second person. Actual paging integration is configured and tested with the deployment platform when operational work begins.
