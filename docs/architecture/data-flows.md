# Data Flows and Failure Boundaries

## Authoritative action flow

1. Cloudflare terminates TLS and applies WAF, DDoS, bot, size, and rate controls.
2. The Edge Gateway creates or validates `X-Request-ID`, adds origin authentication, and routes to the ALB.
3. FastAPI verifies Supabase JWT claims, resolves identity and tenancy, authorizes the named action, and validates the request schema.
4. The application loads the pinned definition and state version.
5. The pure runtime evaluates the action with supplied logical time and seed.
6. MongoDB commits state, ledger, idempotency, audit, and outbox data within the documented transaction boundary.
7. The outbox publisher sends committed events to MSK; consumers update projections and launch follow-up work.
8. The response returns the receipt, state version, definition digest, event IDs, and request ID.

## Data authority table

| Data | Authority | Non-authoritative copies |
|---|---|---|
| Player state, ledgers, entitlements, definitions metadata | MongoDB Atlas | Valkey cache, R2 exports |
| Definition bundles, assets, simulation artifacts, analytics lake | Cloudflare R2 | CDN/cache variants |
| Domain events during retention | MSK | Consumer projections |
| Task delivery | Amazon MQ RabbitMQ | Celery result backend |
| Cache, leases, presence, queue indexes, leaderboard projections | Valkey | None; rebuild from durable authorities |

## Failure boundaries

| Failure | Required behavior | Evidence owner |
|---|---|---|
| Cloudflare outage | Follow edge incident runbook; never expose origin directly | `sre_owner` |
| API task failure | ALB does not retry mutations; client repeats the same idempotency key | `api_owner` |
| MongoDB uncertainty | Return `operation_status_unknown`; reconcile by idempotency record | `data_owner` |
| MSK outage | Keep committed outbox rows pending until publication succeeds | `platform_operations_owner` |
| RabbitMQ/Celery failure | Redelivery with task-level idempotency | `platform_operations_owner` |
| Valkey failure | Rebuild cache; value-changing locks fail closed | `sre_owner` |
| R2 failure | Do not make a definition available until write and read-back verification pass | `release_manager` |

Sequence details are in the diagrams in `docs/architecture/diagrams/`.
