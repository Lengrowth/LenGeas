# Server deployment runbook

This runbook prepares the Phase 01 local dependency stack for an authorized non-production server. It does not provision cloud resources, create credentials, or expose services publicly.

The developer workstation must not install or run Docker for this handoff. Use `tools/dev/server_bundle.py` to verify the transfer bundle; execute the Docker commands below only on the authorized server.

## Prerequisites

- Linux host with Docker Engine and the Compose v2 plugin installed at approved versions.
- A reviewed checkout of the LenGeas repository and access to the server-side secret manager.
- A server-only environment file derived from `.env.example`; credentials are injected by the host secret manager and are never committed.
- Firewall rules limiting the loopback-bound ports in `compose.yaml` to the operator tunnel or server-local clients.

## First command

From the repository root, run the following on the authorized non-production server:

```sh
docker compose --project-name lengeas-local --env-file .env --file compose.yaml config --quiet
```

## Startup and verification

```sh
python3 tools/dev/task_runner.py local-up
python3 tools/dev/task_runner.py local-smoke
```

The smoke command must produce real evidence for the MongoDB replica-set transaction, RabbitMQ publish/consume, Redpanda publish/consume, MinIO S3 put/get, OTLP-to-Jaeger trace export, and API health/version shell. Preserve stdout/stderr and record the server tool versions in `docs/evidence/phase-01/commands.ndjson`.

## Shutdown and rollback

```sh
python3 tools/dev/task_runner.py local-down
```

The stack is non-production and disposable. If a pinned image fails health checks, stop the stack, retain the raw logs, and open an evidence blocker; do not replace a digest with a mutable tag.
