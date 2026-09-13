# ADR-0004 — Celery with Amazon MQ RabbitMQ background work

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Workflow owner; SRE owner
- Supersedes: none
- Superseded by: none

## Context

Publishing, migrations, notifications, support exports, maintenance, and simulation orchestration need durable task delivery, retries, queue classes, and idempotent handlers without extending request latency.

## Decision

Use Celery 5.6 with Amazon MQ for RabbitMQ as the managed durable broker and Valkey as an expiring result backend. Separate critical, default, simulation, email, and maintenance queues. Task handlers carry idempotency records and bounded retry behavior.

## Consequences

The design matches the selected stack and supports redelivery. It introduces broker operations, task visibility, result expiry, and duplicate-delivery testing.

## Rejected designs

- Direct synchronous execution: rejected because long-running work cannot extend request latency.
- Unmanaged broker: rejected because the selected v1 boundary requires managed Multi-AZ RabbitMQ.

## Validation

Redelivery, queue backlog, poison task, broker outage, task idempotency, result expiry, and recovery tests are required before production rollout.

## Rollout and reversal

Create queues and consumers before enabling producers, then canary task classes. Disable producers, drain or replay durable messages, and return to the prior worker release on rollback.
