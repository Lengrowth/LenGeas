# Operations and Governance

## Ownership

Each service, schema, package, collection, event, dashboard, alert, runbook, and cost center has one accountable owner role and one backup. CODEOWNERS reflects ownership. Orphaned components block release.

For the current delivery model, the repository owner is the sole developer and covers every accountable and backup role. The role split remains a governance and traceability model; it does not imply multiple internal employees. External provider contacts and any policy requiring independent or two-person approval remain separate requirements.

## Change classes

- Standard: backward-compatible application or definition change using normal pipeline.
- High-risk: schema, engine semantics, economy, entitlements, identity, authorization, infrastructure, data migration, multiplayer result, or AI tool policy. It requires domain review and staged canary.
- Emergency: active incident mitigation. It requires incident commander approval, minimal scope, live evidence, rollback, and retrospective within two business days.

## ADR policy

An ADR is required for a technology replacement, system boundary change, new durable store, new trust boundary, breaking contract, new region, new external provider, SLO change, or v1 scope change. Accepted ADRs are immutable; superseding decisions link both records.

## Release management

The release record contains commit, image/Worker/package/schema/definition digests, migrations, test report, security report, approvals, change window, canary metrics, rollback target, operator, and completion status. Application, infrastructure, mechanics, and definition releases can move independently only within compatibility contracts.

## Support operations

Support tools show redacted player/profile state, definition pin, action receipts, ledger, entitlements, sync disputes, matches, and event timeline. Every lookup requires a case ID and is audited. Corrections create compensating actions through approval; direct database edits are forbidden.

## Data governance

The data catalog records owner, source, fields, classification, purpose, lawful basis, region, retention, consumers, and deletion behavior. Schema review rejects unclassified fields. Production exports are encrypted, expiring, watermarked, scoped, and audited.

## Vendor governance

AWS, Cloudflare, MongoDB Atlas, Supabase, Resend, GitHub, Sentry, and model providers have owner, DPA/security assessment, account contacts, status-page integration, exit plan, credential inventory, and annual review. A provider outage runbook states degraded behavior.

## Financial operations

Monthly cost review attributes AWS, Cloudflare, Atlas, Supabase, Resend, Sentry, and AI charges by environment and service. Budget variance above 10% requires an owner explanation and action. Usage quotas protect shared infrastructure from one studio.

## Operational cadence

- Daily: health, integrity, reconciliation, backup, data-quality, and security review by automation.
- Weekly: on-call, dependency, failed-job, capacity, and publication review.
- Monthly: SLO/error budget, cost, access, vulnerability, and vendor incident review.
- Quarterly: access recertification, restore, DR scenario, load test, threat model delta, key rotation exercise.
- Annually: regional recovery, penetration test, privacy program, vendor assessment, and v1 contract review.

## Documentation definition of done

A runbook is complete when an operator unfamiliar with the incident can detect, assess, contain, recover, verify, communicate, and close it in a staging exercise. A design document is complete when requirements, owner, boundaries, data, APIs, failure modes, security, observability, tests, rollout, rollback, and acceptance are explicit.
