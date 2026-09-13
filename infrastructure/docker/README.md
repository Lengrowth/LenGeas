# Pinned local platform

`compose.yaml` is the Phase 01 local platform. Every pulled image is referenced
by an immutable manifest digest; the API shell is built from a digest-pinned
Python base image.

The stack contains MongoDB with a one-node replica-set initializer, Valkey,
RabbitMQ, Redpanda, MinIO plus its bucket initializer, Mailpit, the OpenTelemetry
Collector, Prometheus, Grafana, Jaeger, and the health/version-only API shell.

Use the task runner from the repository root:

```text
task local:up
task local:smoke
task local:down
```

`tools/dev/local.py` creates an ignored `.env` with ephemeral local-only
credentials when needed. No credential value is stored in Git. `local:down`
removes the Compose volumes, so it is the reset/rollback boundary for local
state.

Direct Compose use requires the same variables to be supplied in the process
environment: `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`,
`MINIO_ROOT_USER`, and `MINIO_ROOT_PASSWORD`. The supported one-command path
is the task runner, which provisions those values outside the repository.
