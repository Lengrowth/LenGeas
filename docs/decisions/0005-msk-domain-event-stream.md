# ADR-0005 — MSK domain event stream

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Eventing owner; Data owner
- Supersedes: none
- Superseded by: none

## Context

Committed facts need ordered, replayable, at-least-once delivery to projections, analytics, notifications, and downstream workflows while each consumer remains idempotent.

## Decision

Use Amazon MSK Serverless as the domain event stream with private networking, IAM authentication, TLS, topic policies, monitored retention, and documented partition keys. MongoDB outbox rows are the commit authority; publication is asynchronous.

## Consequences

The stream supports replay and consumer isolation. It requires outbox monitoring, schema/version compatibility, lag alerts, retention management, and replay runbooks.

## Rejected designs

- Direct collection polling for all consumers: rejected because it couples consumers to persistence and removes the event contract.
- RabbitMQ as the domain-event authority: rejected because RabbitMQ remains the Celery task broker in the selected boundary.

## Validation

Outbox stall, duplicate delivery, ordering, replay, consumer lag, retention, topic policy, and recovery tests are required before production rollout.

## Rollout and reversal

Create topics and consumers before enabling outbox publication. Stop publication on rollback, retain outbox rows, and replay into compatible consumers after recovery.
