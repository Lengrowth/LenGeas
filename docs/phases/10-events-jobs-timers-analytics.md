# Phase 10 — Events, Jobs, Timers, and Analytics

## Goal

Operationalize the event stream, Celery work, universal timers, analytics lake, and data-quality controls.

## Entry

Phase 09 is accepted.

## Tasks

- [ ] **P10-T01 — Deploy outbox publisher and MSK.** Configure schemas, topics, partition keys, retention, IAM, idempotent producers, lag metrics, replay, and dead-letter streams. Depends on P05-T07, P02-T05. Evidence: outage/backlog replay.
- [ ] **P10-T02 — Build event consumers.** Implement inbox dedupe, projections, quest/achievement consumers, causation, retries, poison handling, and replay-safe side effects. Depends on P10-T01, P07-T02–T03. Evidence: duplicate/reorder suite.
- [ ] **P10-T03 — Deploy Celery.** Configure RabbitMQ quorum queues, routing, publisher confirms, result expiry, retries, time limits, Flower-equivalent monitoring, dead letters, and task idempotency. Depends on P02-T05. Evidence: broker failover test.
- [ ] **P10-T04 — Implement scheduler and timers.** Build partition scan, Valkey leases, stable firing keys, recurring schedules, catch-up, cancellation, and due-time SLO. Depends on P10-T03, P09-T06. Evidence: duplicate/failover/time-travel tests.
- [ ] **P10-T05 — Build analytics catalog/ingestion.** Validate standard/custom events, pseudonymize, classify, dedupe, batch, and write hourly Parquet partitions to R2. Depends on P10-T01, P02-T06. Evidence: catalog and partition tests.
- [ ] **P10-T06 — Build governed query layer.** Enforce studio/game scope, privacy threshold, partition pruning, saved metrics, and audited exports. Depends on P10-T05. Evidence: access/performance tests.
- [ ] **P10-T07 — Implement data quality.** Check schema, duplicates, lag, gaps, sequences, sample ratio, and ledger reconciliation; mark invalid dashboards/results. Depends on P10-T05–T06, P06-T07. Evidence: injected-failure report.
- [ ] **P10-T08 — Complete telemetry.** Propagate trace context through API, outbox, MSK, Celery, timers, analytics, and R2; add dashboards and alerts. Depends on P10-T01–T07. Evidence: end-to-end trace.
- [ ] **P10-T09 — Build notification service.** Implement versioned templates, in-game inbox, Resend, Amazon SNS APNs/FCM, VAPID web push, preferences, consent, quiet hours, frequency caps, schedules, dedupe, provider receipts, retry/dead-letter, invalid-token cleanup, reward-claim action, and audit. Depends on P10-T03–T05, P08-T09. Evidence: channel/provider failure matrix.

## Exit gate

Outages and duplicate deliveries produce no duplicate side effects; backlogs replay; timer and event SLOs pass; analytics partitions reconcile with server business events and enforce tenant/privacy boundaries.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 09 handoff and the API/event/job, analytics, persistence, security, SRE, and infrastructure contracts.

### Exact outputs

MSK topic/schema/IAM Terraform; outbox publisher; inbox library; event projectors; Celery app/queue/task policy; timer scheduler and firing workers; analytics catalog/validation/redaction/batching/Parquet writer; governed query API; data-quality jobs; dashboards/alerts; and broker/timer/analytics runbooks and tests.

Provision Cloudflare Pipelines, R2 Data Catalog Iceberg tables, R2 SQL credentials/query adapter, export fallback, and catalog compaction/snapshot policy through Terraform/Wrangler automation. P10-T09 adds `packages/domain/notifications/`, notification API/provider adapters, templates, device-token store, runbooks, and tests.

MSK topics use `lengeas.<env>.<domain>.v1`; player partition key is `game_id:player_id`, match key is `match_id`. Celery queues are `critical`, `default`, `simulation`, `email`, and `maintenance`. Timer firing key is `timer_id:scheduled_due_at`. Analytics R2 partitions use `environment/game_id/date/hour/event_type/schema_major`.

Create checked-in event and task catalogs. The event catalog records producer, consumers, schema digest, partition key, retention, PII class, analytics mapping, owner, dashboard, and replay procedure. The task catalog records queue, idempotency key, retry schedule, time limits, dead-letter policy, owner, and runbook.

### Required failure tests

Stop MSK while committing actions and drain the outbox after restart. Duplicate/reorder/poison events and rebuild projections. Fail RabbitMQ and kill Celery after an external receipt but before acknowledgment. Race timer schedulers, lose a Valkey lease, repeat one due delivery, and jump logical time. Inject PII, bad schemas, duplicates, late events, missing partitions, sample-ratio mismatch, and ledger mismatch into analytics.

### Handoff to Phase 11

Provide event/task/timer catalogs and APIs, simulation queue SLA, R2 Iceberg/R2 SQL analytics contract, notification/template/channel APIs, data-quality status API, metrics/alerts, replay commands, and failure-tested runbooks.
