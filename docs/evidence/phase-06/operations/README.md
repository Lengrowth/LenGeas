# Phase 06 operational evidence

Mongo index creation is exposed by each repository's `ensure_indexes` method
for documented collections only. Reconciliation reports are persisted to
`audit_logs`; alert events are written to `outbox_events`; repair proposals are
marked `requires_owner_review` and do not mutate value state. Operational
response steps are in `docs/runbooks/economy-inventory-support.md`.

The local workstation has no Docker executable, no `MONGODB_URI`, and no
`CELERY_BROKER_URL`. Consequently the Mongo replica-set transaction drill,
Celery/RabbitMQ delivery/retry check, Mongo reconciliation corruption drill,
and live Apple/Google sandbox matrix could not run. They remain explicit
Phase 06 risks.
