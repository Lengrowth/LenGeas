# Phase 01 Handoff

## Status

`in_review` — the repository foundation, server runtime, public HTTPS endpoint, live CI gates, and keyless release evidence are implemented. This handoff is for review and does not claim repository-owner acceptance.

## Operational state

The repository contains a digest-pinned Compose stack for MongoDB replica-set transactions, Valkey, RabbitMQ, Redpanda, MinIO, Mailpit, OpenTelemetry Collector, Prometheus, Grafana, Jaeger, and an API health/version shell. Docker was not installed or run locally after the repository owner directed that local execution not occur. `tools/dev/server_bundle.py` creates a hash manifest for the server transfer set without invoking Docker. Server execution is described in `infrastructure/docker/SERVER-DEPLOYMENT.md`.

The authorized AWS host `i-0e826e65d7f5df890` runs the digest-pinned stack and passed the complete server smoke, integration harness, server-local E2E harness, public HTTPS health/version checks, and public E2E harness. This `us-east-1` host is a temporary Phase 01 validation environment, not the Phase 02 production topology. Cloudflare manages the authoritative DNS record, which is currently DNS-only; public traffic reaches Caddy on the EC2 origin directly. The developer workstation did not install or run Docker. Server execution is described in `infrastructure/docker/SERVER-DEPLOYMENT.md` and `infrastructure/aws/README.md`.

## Public interfaces and versions

- Root commands: `Taskfile.yml` and `tools/dev/task_runner.py`.
- Evidence schema: `packages/schemas/evidence/phase-manifest.schema.json`; generated Python/TypeScript outputs are under `packages/shared-types/generated/`.
- Exact local pins: Python `3.13.5`, Node `22.16.0`, pnpm `11.20.0`, uv `0.11.29`, Terraform `1.15.8`, go-task `3.53.1`.
- Container images are referenced by immutable digests in `compose.yaml`.
- CI workflows are `.github/workflows/{verify,release,dependency-review,codeql}.yml`.

## Migrations, flags, and rollback

No persistent migrations or deployments were applied. No feature flags exist. Rollback is the prior Git commit plus the prior image digest; do not mutate a digest to recover a failed run.

## Dashboards, alerts, and runbooks

Local Prometheus, Grafana, and Jaeger services are configured by Compose. Server startup, smoke, and shutdown procedures are in `infrastructure/docker/SERVER-DEPLOYMENT.md`. No production dashboard, alert, or cloud run has been claimed.

## Credentials and external setup

No credentials are stored in Git or on the server source archive. The server bootstrap generates its private `.env` on-host. Server-local E2E passed with `LENGEAS_E2E_BASE_URL=http://127.0.0.1:8000`, and public E2E passed with `LENGEAS_E2E_BASE_URL=https://games.lengrowth.com`.

## Known blockers

See `blockers.md` for BLK-01 through BLK-05. The implementing agent records them as resolved; the review agent must independently verify that the temporary direct-origin endpoint, local Docker constraint, and remaining dependency advisories do not violate the Phase 01 gate. Review and explicit repository-owner acceptance remain pending.

## Exact next command

```text
task phase:gate PHASE=01
```

## Prohibited assumptions

Do not treat local static validation as live service evidence, do not assume a GitHub remote or OIDC identity exists, do not run Docker on the developer workstation, do not expose the local services publicly, and do not start Phase 02 before Phase 01 is accepted.
