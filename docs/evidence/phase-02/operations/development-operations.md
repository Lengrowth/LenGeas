# Development operations evidence

The current Phase 02 operational boundary is the existing single-host
development environment. The active runbooks are:

- `docs/runbooks/development-host-backup.md` — backup expectations and recovery
  boundary.
- `docs/runbooks/development-host-incident.md` — outage, compromise, exposure,
  and resource-exhaustion response.
- `docs/runbooks/credential-rotation.md` — secret and operator credential
  rotation.
- `infrastructure/aws/README.md` and
  `infrastructure/docker/SERVER-DEPLOYMENT.md` — deployment, health, restart,
  and rollback procedure.

The recorded development evidence is read-only: the host identity/region/AZ,
storage and IAM limitations, network boundary, and public `/health` and
`/version` checks are in `aws-inventory-2026-09-13.md` and `commands.ndjson`.
No backup restore, incident, failover, or production recovery exercise is
claimed. Any future exercise must use synthetic data and redacted output.
