# Observability, SRE, and Disaster Recovery

## Telemetry

Phase 02 provides development health checks and local stack telemetry only. Production SLOs, paging, managed telemetry, backup guarantees, and regional recovery begin only after the ADR-0011 production activation gate; the current single host makes none of those claims.

Cloudflare creates the edge request ID and W3C trace context. FastAPI, MongoDB calls, Valkey calls, Celery, MSK producers/consumers, R2 access, and realtime services propagate trace/correlation/causation IDs. Logs are structured JSON.

Required fields are timestamp, environment, service, version, region, severity, request/trace/span IDs, studio/game/player pseudonymous IDs when relevant, action/event/task/match IDs, definition digest, duration, outcome, and stable error code.

## SLOs

| Service | SLI and objective |
|---|---|
| Player/API availability | 99.95% successful eligible requests monthly |
| Studio availability | 99.9% successful eligible requests monthly |
| Player/API latency | p95 <= 250 ms and p99 <= 750 ms |
| Action integrity | 99.9999% action receipts reconcile with state and ledger |
| Event publication | 99.9% committed outbox events reach MSK within 60 seconds |
| Timer firing | 99.9% server timers begin processing within 30 seconds of due time |
| Realtime input | p99 accepted-input processing <= 50 ms in-region |
| Publishing | 99% non-simulation pipeline runs finish within 15 minutes |

Eligible requests exclude documented client errors and planned load tests. Maintenance does not exclude externally visible downtime.

## Alerts

Alerts use multi-window burn rates for SLOs plus direct integrity alerts for ledger imbalance, duplicate grant, outbox stall, sync quarantine surge, purchase reconciliation gap, definition digest mismatch, unauthorized access, Atlas replication health, queue depth/age, consumer lag, capacity exhaustion, certificate expiry, backup failure, and cost anomaly.

Every page names severity, owner, user impact, dashboard, runbook, and escalation. Alerts without actionable response are removed or converted to dashboards.

## Capacity management

Dashboards track requests, actions, transactions, connections, matches, ticks, MongoDB operations/storage, cache hit ratio, RabbitMQ depth, Kafka lag, R2 bytes/operations, ECS CPU/memory/capacity, simulation queue, and per-studio cost. Quarterly load tests project 12-month capacity with a 2x safety factor.

## Backups

- MongoDB Atlas: continuous backup with point-in-time restore.
- R2: object versioning, lifecycle, and daily inventory digest.
- Terraform: versioned KMS-encrypted S3 backend with lockfile.
- Configuration: Git plus signed release artifacts.
- Valkey, RabbitMQ, and MSK are recovered from durable authorities and retained streams; cache is never treated as backup.

## Disaster recovery

The regional RTO is 4 hours and persistent-data RPO is 15 minutes. The DR runbook provisions ECS, ALB, networking, Valkey, RabbitMQ, MSK, secrets, and Atlas restore connectivity in `eu-west-1` from Terraform. Cloudflare origin routing changes only after data restore, integrity checks, smoke tests, and incident commander approval.

Quarterly DR exercises alternate between control-plane loss, primary-region loss, Atlas restore, R2 object recovery, secret rotation, and corrupted publication. Annual exercise performs full regional recovery.

## Runbooks

Minimum runbooks cover API errors/latency, Atlas degradation, cache failure, queue backlog, Kafka lag, outbox stall, timer backlog, Cloudflare incident, R2 failure, auth outage/key rotation, purchase provider failure, ledger imbalance, realtime capacity, AZ loss, region loss, compromised credential, bad definition release, bad application release, and privacy request failure.

## Error budgets

When a service exhausts its 30-day error budget, feature releases affecting it stop. The owner prioritizes reliability work until the burn rate returns within policy. Security fixes and incident mitigations remain deployable.
