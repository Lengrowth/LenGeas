# Phase 02 — Development Cloud Foundation

## Goal

Adopt and document the existing low-cost AWS development host as the reproducible cloud foundation for platform development without provisioning a production estate before a workload exists.

## Entry

Phase 01 is accepted. The existing `LenGeas-Phase01-Server` is a running `t3.medium` in `us-east-1a`, and `games.lengrowth.com` is its temporary development endpoint. ADR-0011 is accepted.

## Scope boundary

Phase 02 does not provision staging, production, disaster-recovery, multi-account, three-AZ, ECS, NAT gateway, MongoDB Atlas, managed Valkey, Amazon MQ, MSK, managed observability, Supabase, or Resend infrastructure. Those remain production-target capabilities and require a later rollout ADR based on a real workload and approved cost model.

The provider-pinned Terraform modules in `infrastructure/terraform/` are disabled reference plans. They are not active infrastructure, are not required to be applied for this phase, and must be refreshed against current providers at the production activation gate.

## Tasks

- [ ] **P02-T01 — Inventory the active development foundation.** Verify and record the existing instance name, region/AZ, size, lifecycle state, storage posture, instance-profile posture, monitoring, ingress boundary, authoritative DNS state, and public health/version endpoints. Evidence: redacted inventory and risk register.
- [ ] **P02-T02 — Preserve reproducible delivery.** Validate the digest-pinned server bundle, source-transfer procedure, on-host bootstrap, secret generation boundary, rollback procedure, and cross-platform repository commands. Do not install or run Docker on the developer workstation. Evidence: bundle manifest and recovery runbook.
- [ ] **P02-T03 — Document the development network boundary.** Confirm that only Caddy is publicly reachable on HTTP/HTTPS, service dependencies bind to loopback, and SSH is restricted to the operator address. Record the DNS-only direct-origin exception and prohibit production/customer data. Evidence: redacted security-group and bind-contract review.
- [ ] **P02-T04 — Adopt the existing compute envelope.** Keep the single `t3.medium` in `us-east-1a`; do not move, resize, duplicate, or repurpose it as production. Verify service health and document capacity, availability, patching, and recovery limitations. Evidence: live health/version and capacity record.
- [ ] **P02-T05 — Retain development data services.** Use the Phase 01 single-host Compose dependencies only for synthetic development data. Verify that MongoDB, Valkey, RabbitMQ, Redpanda, MinIO, Mailpit, telemetry, and API services are not independently public. Evidence: inherited server smoke plus current configuration review.
- [ ] **P02-T06 — Preserve endpoint continuity.** Keep `games.lengrowth.com` operational and truthfully label it DNS-only/direct-origin. Do not enable a production cutover, origin allowlist, paid WAF/bot products, or new edge worker until the rollout gate. Evidence: DNS classification and HTTP 200 health/version checks.
- [ ] **P02-T07 — Record deferred provider activation.** Maintain a provider register for Cloudflare, Atlas, Supabase, Resend, Sentry, and AWS production services, including required credentials, plan capabilities, expected data, migration boundary, and activation owner decision. Do not create those resources. Evidence: provider activation matrix without secret values.
- [ ] **P02-T08 — Establish minimal development operations.** Document log access, health checks, disk/capacity checks, restart, backup expectations, credential rotation, incident handling, and cost review for the single host. Record that production SLO, RTO, RPO, paging, and regional recovery are not claimed. Evidence: exercised read-only checks and runbooks.
- [ ] **P02-T09 — Lock the production activation gate.** Preserve the candidate production Terraform as disabled reference material, document its projected topology and risks, and require a new owner-approved rollout ADR plus capacity, cost, security, migration, and rollback evidence before any apply. Evidence: ADR-0011, disabled-root checks, and production activation checklist.

## Exit gate

The repository owner reviews the infrastructure, security, SRE, and financial responsibility lenses and confirms that:

- the actual `us-east-1a` development host and endpoint are documented accurately;
- the development deployment and rollback procedure remains reproducible;
- no new recurring-cost production infrastructure was created;
- no customer or production data exists;
- current development risks are explicit and do not masquerade as production controls;
- all production-target Terraform roots remain disabled; and
- production activation requires a later owner-approved rollout ADR and full live qualification.

The implementing AI marks Phase 02 `in_review`. Only the repository owner may record `accepted`.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read the Phase 01 handoff, ADRs 0001–0005 and 0008–0011, plus the architecture, technology, security, SRE, and infrastructure documents.

### Exact outputs

- Updated current-versus-target architecture and infrastructure documents.
- `docs/decisions/0011-development-first-infrastructure-activation.md`.
- Redacted current-state, security, endpoint, cost, provider-readiness, and recovery evidence under `docs/evidence/phase-02/`.
- Development operations updates under `infrastructure/aws/` and `docs/runbooks/`.
- Disabled-by-default production-target Terraform and static policy checks under `infrastructure/terraform/` and `infrastructure/policies/`.

### Required scenarios

- Read-only AWS inventory identifies `LenGeas-Phase01-Server` as a running `t3.medium` in `us-east-1a`.
- Public `https://games.lengrowth.com/health` and `/version` return HTTP 200.
- Configuration review proves dependency services are loopback-only and no secret is stored in Git or evidence.
- Server bundle and rollback records identify immutable source/image inputs.
- Static checks prove every future production root defaults to disabled.
- Read-only inventory confirms no Phase 02 production estate was created.
- The production activation checklist fails closed without a rollout ADR and owner-approved cost/capacity decision.

Live ECS, managed-service failover, three-AZ loss, Atlas PrivateLink, Cloudflare origin-denial, and regional DR scenarios are deferred production qualification requirements. Static Terraform cannot be reported as live evidence.

### Handoff to Phase 03

List the current development endpoint, source/deployment command, local service boundaries, secret names, log/health procedures, current risks, and deferred provider activation points. Phase 03 develops against synthetic data and the existing development stack; it must not assume production topology, SLOs, managed services, or customer data.
