# Staging failover and replay

Deferred production exercise: run only against an activated staging or isolated environment with synthetic data. Capture start/end UTC, target service, request ID, and outcome. The Phase 02 single-host development foundation does not provide these services or failover guarantees.

Exercise Atlas restore/failover, Valkey automatic failover, RabbitMQ redelivery/backlog, MSK consumer pause and replay, and ECS capacity replacement. Verify idempotency, no duplicate value, trace continuity, and alert routing. A scenario is not passed from a dry run or a static plan.
