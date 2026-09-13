# C4 Container View

The container view preserves the selected Cloudflare/AWS ownership split. Edge services apply policy and route traffic; canonical game and platform rules execute in AWS services; durable authorities remain in MongoDB Atlas and R2.

```mermaid
C4Container
  title LenGeas container view
  System_Boundary(platform, "LenGeas") {
    Container(edge, "Edge Gateway Worker", "Cloudflare Worker", "Request ID, coarse rate, body limit, origin authentication, routing")
    Container(studio, "Game Studio", "Next.js 16 / OpenNext / Workers", "Human control plane using public APIs")
    Container(api, "platform-api", "FastAPI on ECS", "Auth, tenancy, definitions, actions, operations, support")
    Container(realtime, "realtime-gateway", "WebSocket service on ECS", "Connection, heartbeat, protocol validation, routing")
    Container(match, "match-service", "ECS service", "Authoritative match lifecycle and deterministic simulation")
    Container(workers, "Workers and projectors", "Celery, MSK consumers", "Publishing, jobs, projections, notifications, maintenance")
    Container(runtime, "Pure runtime", "Python library", "Conditions, formulas, plans, effects, rewards, timers")
    ContainerDb(mongo, "MongoDB Atlas", "Dedicated clusters", "Durable documents, state, ledgers, outbox, audit")
    ContainerDb(valkey, "ElastiCache Valkey", "TLS Multi-AZ", "Cache, leases, rate counters, presence, projections")
    ContainerQueue(rabbit, "Amazon MQ RabbitMQ", "Durable quorum queues", "Celery task delivery")
    ContainerQueue(msk, "Amazon MSK Serverless", "Kafka-compatible stream", "Replayable domain events")
    ContainerDb(r2, "Cloudflare R2", "Private buckets", "Bundles, assets, simulation artifacts, analytics, exports")
  }
  Rel(studio, api, "Definition and operation API")
  Rel(edge, api, "Authenticated origin route")
  Rel(edge, realtime, "Authenticated WebSocket route")
  Rel(api, runtime, "Builds deterministic execution plan")
  Rel(api, mongo, "Scoped reads and transactional writes")
  Rel(api, valkey, "Cache, locks, counters")
  Rel(api, rabbit, "Publishes background work")
  Rel(api, msk, "Publishes committed outbox events")
  Rel(workers, mongo, "Owns worker persistence boundaries")
  Rel(workers, r2, "Stores and reads artifacts")
  Rel(match, valkey, "Routing and presence")
  Rel(match, mongo, "Checkpoints and match history")
  Rel(realtime, match, "Routes session inputs")
```

Services own documented APIs and collections. A service does not import another service's persistence repository.
