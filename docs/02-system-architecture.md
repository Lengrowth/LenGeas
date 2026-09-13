# System Architecture

## Current development topology

Phase 02 runs the synthetic development platform on the existing `LenGeas-Phase01-Server`, a single `t3.medium` EC2 instance in `us-east-1a`. Cloudflare is authoritative for `games.lengrowth.com`, but the record is DNS-only and traffic reaches Caddy on the EC2 origin directly. The pinned Compose stack supplies development dependencies on that host. This topology has no high-availability, production SLO, private-origin, or regional-DR claim and may not contain customer or production data.

## Target production topology

```text
Players / Studio users
        |
Cloudflare DNS, TLS, DDoS, WAF, Bot Management, Turnstile, Rate Limiting
        |
        +-- studio.lengeas.com -> Next.js on Cloudflare Workers
        |
        +-- api.lengeas.com -> Edge Gateway Worker -> AWS public ALB
        |                                           |
        |                               ECS on EC2 private subnets
        |                                API / realtime / workers
        |                                  |       |       |
        |                         MongoDB Atlas  Valkey  Amazon MQ
        |                         via PrivateLink         RabbitMQ
        |                                          |
        |                                    MSK Serverless
        |
        +-- assets.lengeas.com -> private Cloudflare R2
```

The current candidate production design uses AWS `eu-central-1` as primary and `eu-west-1` as disaster recovery, with production spanning three availability zones. These regions and resources are not deployed in Phase 02. Before production activation, a rollout ADR must confirm or supersede the region choice using the actual workload, capacity, cost, provider, security, and data-residency requirements. Staging and production then use separate accounts and provider projects.

## Responsibility split

| Capability | Owner | Rule |
|---|---|---|
| Public DNS, TLS, CDN, WAF, DDoS, bots, edge rate limits | Cloudflare | No public hostname bypasses Cloudflare |
| Studio compute | Cloudflare Workers | Next.js is deployed through OpenNext; Node-only incompatibilities are prohibited |
| API gateway edge policy | Cloudflare Worker | Adds request ID, coarse rate limit, body limit, origin authentication, and routing; it does not execute canonical game rules |
| Static assets, published definition bundles, simulation artifacts, analytics lake | Cloudflare R2 | Buckets are private; access uses Workers or scoped S3 credentials |
| Asset image transformation | Cloudflare Images | Only approved R2 originals are transform sources |
| Analytics ingestion and query | Cloudflare Pipelines, R2 Data Catalog, R2 SQL | Pipeline writes Iceberg tables; governed API is the only Studio/agent query path |
| Canonical application compute | AWS ECS on EC2 | Docker images from private Amazon ECR; tasks run in private subnets |
| HTTP and WebSocket origin | AWS Application Load Balancer | Inbound traffic accepts Cloudflare origin traffic only |
| Durable game and platform documents | MongoDB Atlas on AWS | Dedicated clusters reached through AWS PrivateLink |
| Cache, locks, presence indexes, leaderboards | Amazon ElastiCache for Valkey | Never the only durable copy of player value |
| Background task broker | Amazon MQ for RabbitMQ | Celery commands and workflow tasks |
| Domain event stream | Amazon MSK Serverless | Ordered, replayable integration events |
| Secrets | AWS Secrets Manager and Cloudflare Secrets Store | No secret is stored in Git, image layers, or Terraform variables in plaintext |
| Authentication | Supabase Auth | Uses asymmetric signing keys; FastAPI verifies JWTs from JWKS |
| Email | Resend | Only the notification service possesses the API key |
| Infrastructure definitions | Terraform | AWS, Cloudflare, MongoDB Atlas, Supabase configuration, and Resend DNS records are reviewed as code |

## Runtime services

- `platform-api`: FastAPI REST API for Studio, clients, definitions, players, actions, operations, and support.
- `realtime-gateway`: WebSocket connection, session routing, heartbeat, and compact protocol validation.
- `match-service`: authoritative match lifecycle and deterministic match simulation.
- `celery-worker-general`: publishing, migrations, notifications, support exports, and maintenance.
- `celery-worker-simulation`: isolated CPU-bound simulations on a separate ECS capacity provider.
- `event-projector`: MSK consumers for quests, achievements, projections, search, analytics, and notifications.
- `scheduler`: single logical scheduler protected by a distributed lease; emits due timer tasks.
- `analytics-ingest`: validates, redacts, batches, and writes analytics objects to R2.
- `asset-worker`: scans quarantined uploads, validates ownership metadata, creates approved asset records, and requests image variants.
- `notification-service`: resolves versioned localized templates and sends inbox, Resend email, Amazon SNS mobile push, or VAPID web push.

Each service owns a documented API and collections. A service cannot import another service's persistence repository.

## Request path

1. Cloudflare terminates public TLS and applies WAF, DDoS, bot, request-size, and rate-limit policies.
2. The Edge Gateway creates or validates `X-Request-ID`, attaches an origin-authenticated header, and forwards to the AWS ALB.
3. The ALB terminates origin TLS and routes to an ECS service target group.
4. FastAPI verifies the Supabase JWT, resolves internal identity and tenancy, authorizes the action, and validates the request schema.
5. The application service loads the pinned published definition and current state version.
6. The pure runtime evaluates conditions, costs, effects, and rewards.
7. The persistence unit commits state, ledger, idempotency record, audit metadata, and outbox events atomically where MongoDB transaction boundaries require it.
8. The response includes action result, new state version, definition digest, emitted event IDs, and request ID.
9. An outbox publisher sends events to MSK. Consumers update projections without extending request latency.

## Failure boundaries

- Cloudflare failure: DNS failover does not expose the origin; operators follow the Cloudflare edge incident runbook.
- API task failure: ALB retries no mutation. Clients retry only with the same idempotency key.
- MongoDB uncertainty: mutation returns `operation_status_unknown`; reconciliation checks the idempotency record before another execution.
- MSK failure: committed outbox rows remain pending until publication succeeds.
- Celery failure: RabbitMQ redelivers; task handlers use task-level idempotency records.
- Valkey failure: cached data is rebuilt; locks fail closed for value-changing operations.
- R2 failure: publishing does not mark a version available until bundle write and read-back verification succeed.

## Environments

`development`, `testing`, `staging`, and `production` are separate logical environments. Staging and production use separate AWS accounts, Atlas projects/clusters, Supabase projects, Cloudflare Worker environments, R2 buckets, RabbitMQ brokers, MSK clusters, Valkey replication groups, encryption keys, and credentials. Production data never enters lower environments. Sanitized synthetic fixtures are the only supported test data.

Phase 02 adopts the temporary Phase 01 host as the active development foundation. Separate production-target Terraform roots remain disabled reference material. They must not be applied until a later rollout ADR, current provider validation, capacity evidence, and explicit owner cost approval exist. The development endpoint remains available until a replacement is verified and the owner authorizes retirement.
