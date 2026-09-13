# API, Events, Jobs, and Timers

## REST API

- Base path is `/api/v1`.
- JSON is the default representation; canonical bundles and exports use signed R2 downloads.
- Commands accept `Idempotency-Key`; value-changing commands require it.
- Collection pagination uses opaque signed cursors.
- Optimistic updates use `If-Match` with state version ETags.
- Long work returns `202 Accepted` with an operation resource.
- Public endpoints publish OpenAPI 3.1 and generated SDK contracts.
- Deprecation requires response headers, documentation, telemetry, and a minimum 180-day support period.

## Action endpoint

`POST /api/v1/games/{game_id}/players/{player_id}/actions/{action_id}` accepts the typed action payload, client-observed state version, logical client timestamp for diagnostics, and idempotency key. The server chooses authoritative logical time and definition.

The response contains status, receipt ID, state version, state patch, ledger references, event IDs, definition digest, server time, and retry guidance.

## Event envelope

```json
{
  "event_id": "uuidv7",
  "type": "quest.completed.v1",
  "occurred_at": "2030-01-01T00:00:00.000000Z",
  "producer": "runtime",
  "studio_id": "uuidv7",
  "game_id": "fixture_game",
  "player_id": "uuidv7",
  "subject_id": "quest_intro",
  "definition_digest": "sha256:...",
  "correlation_id": "uuidv7",
  "causation_id": "uuidv7",
  "traceparent": "00-...-00",
  "payload": {}
}
```

Event schemas are versioned, registered, compatibility-checked, and PII-classified. MSK partitions player events by `game_id:player_id` and match events by `match_id` to preserve subject order.

## Transactional outbox

State mutation and outbox insert share one MongoDB transaction. The publisher leases pending events, publishes with producer idempotence, records broker metadata, and marks them delivered. A daily job detects stalled outbox records. Consumers maintain an inbox keyed by consumer and event ID before producing side effects.

Delivery is at least once. Ordering is guaranteed only within a partition key. Consumers tolerate duplicates and do not depend on global order.

## Celery

Celery runs publishing, migrations, simulation orchestration, emails, webhooks, exports, reconciliation, and maintenance. Queues are separated into `critical`, `default`, `simulation`, `email`, and `maintenance`. Tasks declare retry policy, hard and soft time limits, idempotency scope, queue, and dead-letter handling.

Amazon MQ RabbitMQ is the broker. Value-sensitive queues use durable quorum queues and publisher confirmations. Valkey stores short-lived task results; durable business outcomes live in MongoDB or R2.

## Timers

The timer scheduler scans due MongoDB partitions, claims leases in Valkey, and publishes fire tasks. Firing uses a stable key `<timer_id>:<scheduled_due_at>`. Repeated delivery cannot fire the associated action twice. Recurring timers calculate the next due time from the scheduled time, not worker completion time.

Offline timers use a bounded catch-up plan. A definition states the maximum elapsed window and maximum firings; overflow produces one aggregated action if the timer handler supports aggregation.

## Webhooks

Inbound purchase, ad, Supabase, Resend, and provider webhooks verify signature, timestamp, replay window, and provider event ID before acceptance. The handler stores the raw encrypted payload, returns promptly, and processes through Celery. Outbound webhooks sign body and timestamp, retry exponentially, and expose delivery history.

## Rate classes

Endpoints declare `public_auth`, `guest_create`, `player_read`, `player_action`, `studio_read`, `studio_write`, `simulation_submit`, `publish`, or `support_sensitive`. Cloudflare enforces coarse IP/account limits; FastAPI and Valkey enforce actor, studio, game, player, and action limits.

## Protocol ownership

REST is used for durable control-plane and player commands. WebSocket is used for presence and live sessions. MSK is internal integration only. Celery is internal work dispatch only. None of these protocols substitutes for another.
