# Development host incident handling

This runbook covers suspected compromise, outage, data exposure, or resource
exhaustion on `LenGeas-Phase01-Server`. The host is development-only and may
contain synthetic, non-sensitive data only.

## Immediate response

1. Record UTC time, current source/image digest, endpoint symptoms, and the
   operator who observed the issue. Do not include secrets or customer data.
2. For suspected compromise, restrict the AWS security group to the known
   operator path and remove public application access where safe. Preserve the
   current DNS record; do not enable Cloudflare proxying as an emergency
   substitute for origin protection.
3. Stop or isolate the affected Compose service only after capturing redacted
   status and logs. Do not destroy the host or its evidence impulsively.
4. Rotate any host-generated or operator credential suspected of exposure using
   the credential-rotation runbook. Never paste secret values into the incident
   record.
5. For disk, memory, or CPU exhaustion, capture resource usage, stop nonessential
   synthetic workloads, and roll back to the last known good immutable bundle.

## Recovery and closure

- Restore service with the server deployment and development-host backup
  runbooks, then verify `/health` and `/version`.
- Confirm that dependencies remain loopback-bound and that no customer or
  production data entered the host.
- Record the incident, actions, residual risk, and owner follow-up in the
  repository's operational record. Escalate any suspected real-data exposure
  or credential compromise to the repository owner/security owner before
  resuming development deployment.
- Review the EC2 bill and capacity symptoms; do not add capacity or change the
  production topology from this runbook.

This runbook does not claim production paging, managed detection, forensic
retention, SLO compliance, or regional recovery.
