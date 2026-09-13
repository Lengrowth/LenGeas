# Infrastructure and Deployment

## Current Phase 02 development foundation

The active cloud environment is one EC2 instance:

- Name: `LenGeas-Phase01-Server`
- Region and availability zone: AWS `us-east-1`, `us-east-1a`
- Size: `t3.medium`
- Purpose: synthetic platform development only
- Endpoint: `games.lengrowth.com`
- Edge state: Cloudflare-authoritative DNS, DNS-only; Caddy terminates public HTTPS on the origin
- Runtime: the Phase 01 digest-pinned Compose stack

This instance is sufficient while no game, production workload, customer traffic, or production data exists. Phase 02 keeps it running and does not move, resize, duplicate, or describe it as production.

The host is a single availability-zone failure domain. Its root EBS volume is currently unencrypted, it has no EC2 instance profile, detailed monitoring is disabled, HTTP/HTTPS are public, and SSH is restricted to the operator's recorded `/32`. These are accepted development-stage risks only while all data is synthetic and non-sensitive. Dependency services bind to loopback and are not publicly exposed.

## Development delivery

The repository's server bundle and `infrastructure/aws/phase-01-user-data.sh` remain the canonical development bootstrap. Source is transferred without placing GitHub credentials on the host. The server generates its private `.env` on-host. Rollback selects the prior source commit and immutable image digests.

The developer workstation does not install or run Docker. Server-side commands and public health/version checks provide runtime evidence.

## Development operations and cost

Operations cover public health/version checks, Compose service state, logs, disk/capacity checks, security-group review, restricted operator access, restart, redeployment, and rollback. The owner reviews the existing EC2 and data-transfer bill; Phase 02 adds no new recurring-cost infrastructure or vendor plan.

No production SLO, RTO, RPO, multi-AZ failover, origin isolation, managed backup, or regional disaster recovery is claimed for the development host. Customer and production data are prohibited.

## Deferred production activation target

The following is the candidate v1 production design, not current infrastructure:

- AWS Organizations accounts for management, security, log archive, shared services, nonproduction, staging, and production.
- A candidate primary region of `eu-central-1` and DR region of `eu-west-1`.
- Three availability zones with public ALB subnets, private application subnets, isolated data/endpoint subnets, AZ-local NAT, VPC endpoints, flow logs, and security-group references.
- ECS on EC2 with general, simulation, realtime, and critical-worker capacity providers using ECS-optimized Amazon Linux 2023 ARM64 instances.
- ECR, ALB, Cloud Map, autoscaling, task roles, read-only/non-root tasks, and Systems Manager administration.
- MongoDB Atlas through PrivateLink, ElastiCache for Valkey, Amazon MQ RabbitMQ, MSK Serverless, KMS, Secrets Manager, and private Cloudflare R2.
- Cloudflare-proxied DNS, TLS, WAF, DDoS, available bot controls, Turnstile, rate limits, Workers, authenticated origin routing, and direct-origin denial.
- Supabase Auth, Resend, OpenTelemetry, CloudWatch, managed Prometheus/Grafana, tracing, Sentry, alert routing, backups, and disaster recovery.

ADRs 0001–0005 and 0008–0010 describe the target technology boundaries. ADR-0011 defers their live activation. A later rollout ADR must confirm or supersede the regions and topology against the actual workload and current provider capabilities.

## Deferred Terraform

`infrastructure/terraform/` contains provider-pinned, disabled-by-default reference modules and roots. They are design and static-policy artifacts, not applied infrastructure. Disabled plans may become stale and must be refreshed, costed, reviewed, and live-tested before rollout.

Production activation requires:

1. A concrete workload and capacity forecast.
2. Current provider and plan capability inventories.
3. A consolidated cost estimate and explicit owner ceiling.
4. An accepted rollout ADR confirming regions, accounts, data residency, topology, migration, and rollback.
5. KMS-encrypted versioned state with native lockfiles and restricted GitHub OIDC roles.
6. Live validation of private connectivity, backups, restore, origin denial, observability, failover, and zero drift.
7. A parallel deployment and verified cutover before the development endpoint can be retired.

## Target production delivery

After activation, production releases use immutable image/Worker digests, automated provenance, staged smoke/canary/soak checks, and explicit owner promotion. ECS and Worker traffic shifts must preserve rollback to the prior compatible release. Production data never enters lower environments.

## Acceptance boundaries

Phase 02 accepts only the low-cost development foundation and the fail-closed production activation gate. Phase 17 cannot qualify the platform until the production topology is separately activated and every security, performance, backup, failover, and DR requirement is exercised live. Static Terraform and the development host cannot satisfy production completion.
