# Terraform state recovery

## Detect

Stop all applies when a lock conflict, unexpected state version, or digest mismatch is observed. Page the infrastructure owner and preserve the exact backend key, commit, and command without copying state contents into chat or evidence.

## Assess and contain

Confirm the environment-specific S3 key and that the native `.tflock` object is not held by a running job. Never delete state versions. Deny applies until the owner records whether the event is a stale lock, accidental overwrite, or suspected credential compromise.

## Recover

1. Identify the last known-good S3 object version using a redacted inventory.
2. Copy that version to a quarantined recovery key using an approved break-glass role.
3. Run `terraform show` and schema/provider validation against the quarantined copy.
4. Restore only through a reviewed S3 object operation, then run a read-only plan.
5. Rotate the break-glass credential and record the owner decision.

Recovery is complete only when the next plan is zero-diff or every intended change is explained. This runbook never stores state, credentials, or tokens in Git.
