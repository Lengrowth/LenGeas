# Phase 01 Blockers

## BLK-01 — Docker runtime unavailable

The repository owner directed that Docker must not be installed or run locally. Earlier probes recorded `docker version`, `docker compose version`, `task local:up`, `task local:smoke`, and `task local:down` as unavailable; the Docker Desktop installation attempt was cancelled before completion. MongoDB transaction, RabbitMQ, Redpanda, S3, telemetry, and container health evidence therefore remain unavailable here.

Owner: `platform_operations_owner`; status: open; resolution: execute the server-side Compose smoke procedure on an authorized non-production host and attach the raw output. No local execution is requested.

## BLK-02 — E2E endpoint unavailable

`task test:e2e` failed closed because `LENGEAS_E2E_BASE_URL` is unset. No endpoint or credential was supplied.

Owner: `qa_owner`; status: open; resolution: provide a documented non-production synthetic endpoint and rerun the E2E suite.

## BLK-03 — Remote repository protection unavailable

No Git remote, GitHub owner handle, credentials, live branch protection export, CI run, or signed release-tag verification exists in this workspace. P01-T08 contains only a locally verifiable policy export.

Owner: `infrastructure_owner`; status: open; resolution: connect the repository and export live protected-branch settings and checks without changing the local policy.

## BLK-04 — Sigstore sample verification unavailable

The release metadata and workflow require keyless Sigstore signing, but `cosign` and a CI OIDC identity are unavailable locally. No signature is claimed.

Owner: `release_manager`; status: open; resolution: run the release workflow or an equivalent ephemeral OIDC environment and attach verification output.
