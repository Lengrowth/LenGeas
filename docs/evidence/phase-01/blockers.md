# Phase 01 Blockers

## BLK-01 — Docker runtime unavailable

The repository owner directed that Docker must not be installed or run locally. Earlier probes recorded `docker version`, `docker compose version`, `task local:up`, `task local:smoke`, and `task local:down` as unavailable; the Docker Desktop installation attempt was cancelled before completion. MongoDB transaction, RabbitMQ, Redpanda, S3, telemetry, and container health evidence therefore remain unavailable here.

Owner: `platform_operations_owner`; status: open; resolution: execute the server-side Compose smoke procedure on an authorized non-production host and attach the raw output. No local execution is requested.

## BLK-02 — E2E endpoint unavailable

`task test:e2e` failed closed because `LENGEAS_E2E_BASE_URL` is unset. No endpoint or credential was supplied.

Owner: `qa_owner`; status: open; resolution: provide a documented non-production synthetic endpoint and rerun the E2E suite.

## BLK-03 — Remote repository protection and CI gate unavailable

The remote is now configured and pushed: `origin/main` resolves to `14c6316ae1da4b4fa01de60176aff27b81dbbe1b`. GitHub metadata confirms private repository `guerra2fernando/LenGeas`, default branch `main`, and owner admin permission. The push-triggered verification run `34751926936` completed with `startup_failure`, no jobs, and no check-runs. The authenticated integration returned `403 Resource not accessible by integration` for branch protection and `403 Upgrade to GitHub Pro or make this repository public` for rulesets, so no live protection export is claimed. P01-T08 still contains only a locally verifiable policy export.

Owner: `infrastructure_owner`; status: open; resolution: use the repository owner's GitHub settings/API access to export live protected-branch settings, resolve the Actions startup failure, and attach a successful CI run without weakening the local policy.

## BLK-04 — Sigstore sample verification unavailable

The release metadata and workflow require keyless Sigstore signing, but `cosign` and a CI OIDC identity are unavailable locally. No signature is claimed.

Owner: `release_manager`; status: open; resolution: run the release workflow or an equivalent ephemeral OIDC environment and attach verification output.
