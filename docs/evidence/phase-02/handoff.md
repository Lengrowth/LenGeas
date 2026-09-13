# Phase 02 Handoff

## Status

`accepted` — ADR-0011 aligns the phase with the actual low-cost development environment. Independent review confirmed the required provider activation and development-operations evidence, and the repository owner accepted Phase 02 on 2026-09-14 with no blockers. The existing host is inventoried and healthy, the endpoint is preserved, production-target Terraform remains disabled, and no production estate was created.

## Operational state

`LenGeas-Phase01-Server` is a running `t3.medium` in AWS `us-east-1a`. It runs the Phase 01 digest-pinned Compose stack and serves `https://games.lengrowth.com`. Cloudflare is authoritative for DNS, but the record is DNS-only and public traffic reaches Caddy on the origin directly. `/health` and `/version` returned HTTP 200 during the Phase 02 scope review.

The host remains development-only and may contain synthetic, non-sensitive data only. It is a single-AZ host with a public IP, unencrypted 40 GiB gp3 root volume, no instance profile, basic monitoring, public HTTP/HTTPS, and SSH restricted to the operator `/32`. Dependency services are configured to bind to loopback.

## Interfaces and versions

- Public development endpoint: `https://games.lengrowth.com`.
- Health: `/health`; version: `/version`.
- Deployment and rollback: `infrastructure/aws/README.md`, `infrastructure/docker/SERVER-DEPLOYMENT.md`, and immutable source/image inputs.
- Developer workstation: Docker remains unavailable and must not be installed or run for this phase.
- Production-target provider pins and disabled roots remain under `infrastructure/terraform/` as reference material only.

## Deferred production activation

No AWS Organization, new VPC, NAT gateway, ECS cluster, EC2 capacity, ALB, Atlas cluster, managed Valkey, Amazon MQ, MSK, managed telemetry, staging, production, DR, Supabase, Resend, or new Cloudflare paid capability was created for Phase 02.

Before production rollout, the owner must accept a new rollout ADR that confirms or supersedes the candidate regions/topology using actual workload and cost evidence. The rollout must use reviewed infrastructure as code, encrypted state, restricted OIDC, live security/backup/failover/DR evidence, and a verified parallel cutover before this development endpoint is retired.

## Current risks

- Single host and single availability zone; no availability or DR guarantee.
- DNS-only direct origin; no production origin isolation.
- Unencrypted root storage; synthetic non-sensitive data only.
- No instance profile and no detailed EC2 monitoring.
- Disabled Terraform may drift before activation and must be refreshed.

## Exact next command

```text
uv run --frozen python tools/dev/task_runner.py phase-gate 02
```

## Prohibited assumptions

Do not describe this host as production, do not place customer/production data on it, do not claim Cloudflare proxy/origin protection, do not treat static Terraform as live infrastructure, do not run Docker locally, and do not apply deferred production resources without a rollout ADR and explicit owner cost approval.
