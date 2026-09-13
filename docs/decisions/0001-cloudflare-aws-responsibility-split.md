# ADR-0001 — Cloudflare/AWS responsibility split

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Edge and content delivery owner; Infrastructure owner
- Supersedes: none
- Superseded by: none

## Context

LenGeas needs a public edge and Studio hosting boundary while canonical application state, private services, and durable operational data remain in AWS. The split must preserve origin isolation, data authority, and recovery behavior.

## Decision

Cloudflare owns public DNS, TLS, CDN, WAF, DDoS, bot controls, Turnstile, edge rate limits, Workers, R2, Images, Pipelines, and edge queues. AWS owns the ALB, ECS on EC2 services, MongoDB Atlas connectivity, Valkey, RabbitMQ, MSK, secrets, and canonical application state. No public hostname bypasses Cloudflare; Cloudflare state is never canonical player value or match state.

## Consequences

The boundary gives explicit edge protection and private AWS services. It creates two-provider operational, cost, and outage dependencies; exports, status monitoring, origin controls, and DR exercises are required.

## Rejected designs

- AWS-only edge: rejected because the documented v1 edge control and Worker hosting boundary would be removed.
- Cloudflare-only canonical runtime: rejected because the documented AWS durable-state and compute boundary would be removed.

## Validation

Architecture review, origin-bypass tests, private-bucket tests, Terraform drift checks, edge failure runbook, and regional recovery evidence are required before production rollout.

## Rollout and reversal

Adopt edge routes before public origin exposure, verify authenticated origin traffic, and promote one environment at a time. Reverse by routing to the prior versioned Worker and ECS release; changing providers requires a superseding ADR.
