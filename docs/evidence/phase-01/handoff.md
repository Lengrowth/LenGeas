# Phase 01 Handoff

## Status

`blocked` — the repository foundation and server-ready local stack are implemented, but mandatory runtime, E2E, remote-protection, and Sigstore evidence remain unavailable. This handoff is for independent review and does not claim acceptance.

## Operational state

The repository contains a digest-pinned Compose stack for MongoDB replica-set transactions, Valkey, RabbitMQ, Redpanda, MinIO, Mailpit, OpenTelemetry Collector, Prometheus, Grafana, Jaeger, and an API health/version shell. Docker was not installed or run locally after the repository owner directed that local execution not occur. Server execution is described in `infrastructure/docker/SERVER-DEPLOYMENT.md`.

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

No credentials are stored. Server setup may reference only secret names managed outside Git, including the names from the Phase 00 handoff. A non-production E2E URL must be supplied as `LENGEAS_E2E_BASE_URL` for the E2E suite.

## Known blockers

See `blockers.md` for BLK-01 through BLK-04. They remain actionable and owned.

## Exact next command

```text
task bootstrap
```

## Prohibited assumptions

Do not treat local static validation as live service evidence, do not assume a GitHub remote or OIDC identity exists, do not run Docker on the developer workstation, do not expose the local services publicly, and do not start Phase 02 before Phase 01 is accepted.

