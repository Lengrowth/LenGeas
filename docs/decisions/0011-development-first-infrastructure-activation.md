# ADR-0011 — Development-first infrastructure activation

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owner: Repository owner acting as infrastructure, SRE, security, and financial owner
- Supersedes: Phase 02 activation timing in the delivery plan; target technology ADRs remain unchanged
- Superseded by: none

## Context

LenGeas has no first-party game, customer traffic, production data, or measured production workload. The operational environment is one `t3.medium` EC2 instance named `LenGeas-Phase01-Server` in `us-east-1a`, serving the temporary development endpoint `games.lengrowth.com`. Provisioning the previously planned multi-account, three-AZ ECS, NAT, managed data, observability, staging, production, and DR estate now would create recurring cost and operational work before capacity or reliability demand exists.

## Decision

Phase 02 adopts the existing `us-east-1` host as the active development foundation. It preserves the current endpoint and pinned single-host Compose stack, records the host's security and recovery limitations, and adds no new VPC, NAT gateway, ECS cluster, EC2 capacity, Atlas cluster, Valkey, Amazon MQ, MSK, managed observability, staging, production, or DR resources.

The production topology in ADRs 0001–0005 and 0008–0010 remains the v1 target rather than current deployed state. Its Terraform is disabled reference material and does not satisfy a live production gate. Before production qualification or customer rollout, the owner must accept a rollout ADR based on the actual game/workload, capacity tests, provider capabilities, current prices, security requirements, and data residency. That ADR must confirm or supersede the candidate `eu-central-1` primary and `eu-west-1` DR regions before any production resources are applied.

## Development boundary

- Only synthetic and development data may exist on the current host.
- The direct-origin DNS-only endpoint is a temporary development exception and must never be described as Cloudflare-protected production ingress.
- The host is not highly available and provides no regional DR guarantee.
- Its public IP, unencrypted root volume, lack of an instance profile, basic monitoring, and restricted SSH path are recorded risks. Secrets and customer data remain prohibited.
- No resource expansion or paid vendor activation occurs without a new explicit owner decision.

## Production activation gate

Production-grade infrastructure may be activated only when all of the following exist:

1. A concrete rollout workload and capacity profile.
2. A current cost model and owner-approved ceiling.
3. A reviewed rollout ADR confirming regions, providers, topology, migration, and rollback.
4. Environment isolation and data-classification requirements.
5. Tested Terraform plans, backup/restore, origin protection, observability, and security controls.
6. A migration plan that keeps the development endpoint available until replacement verification completes.

## Consequences

The project avoids premature recurring spend and keeps development simple. Production resilience, private connectivity, managed service failover, origin isolation, and regional recovery are intentionally unavailable until activation. Disabled Terraform may drift from vendor APIs and must be refreshed and revalidated at the rollout gate rather than assumed deployable.

## Validation

Phase 02 validates the actual EC2 identity, region, size, endpoint health, current ingress boundary, deployment/recovery procedure, cost boundary, and absence of newly provisioned production resources. Phase 17 validates the activated production topology; static plans alone cannot satisfy production qualification.

## Rollout and reversal

Continue deploying development builds to the existing host through the Phase 01 server procedure. Roll back by restoring the prior source/image digest. At production activation, build a separate environment, verify it before traffic movement, and retain the development host until the owner explicitly authorizes retirement.
