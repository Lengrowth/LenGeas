# Development host backup and recovery

This runbook applies to `LenGeas-Phase01-Server` in `us-east-1a`. It is for
synthetic, non-sensitive development data only. It is not a production backup,
RPO, or disaster-recovery guarantee.

## Backup expectations

- Git and the immutable image digests are the authoritative source for the
  application and Compose definition. Record the exact source commit and image
  digests before each redeployment.
- The host-only `.env` is generated on the host and must be backed up, if at
  all, through the approved host secret mechanism. Never copy it into Git,
  evidence, a plan, or a workstation archive.
- Compose data is disposable synthetic development state. Do not introduce
  customer, player, production, or real credential data to make a backup test
  meaningful.
- Before maintenance, capture `docker compose ... ps`, the readiness marker,
  disk usage, and the current deployment record. Preserve only redacted output.
- The current root volume is unencrypted and no managed snapshot policy is
  claimed. Do not present an ad-hoc snapshot as a production backup.

## Recovery boundary

1. Confirm the incident or maintenance window and preserve the last known source
   commit, image digests, and redacted service status.
2. If the host is recoverable, use the server deployment procedure to restart
   or roll back to the prior immutable source/image inputs.
3. If the host is lost, rebuild a separate development host through the reviewed
   server bootstrap, restore only synthetic fixtures, regenerate host secrets,
   and run the server smoke plus public health/version checks.
4. Keep `games.lengrowth.com` DNS-only until the replacement endpoint is healthy.
   Do not retire or repoint the existing endpoint as part of an unverified
   recovery.

No automatic restore, encrypted backup, fixed RTO/RPO, or zero-drift recovery is
claimed for this single-host development environment. Production backup and
regional recovery remain rollout/qualification requirements.
