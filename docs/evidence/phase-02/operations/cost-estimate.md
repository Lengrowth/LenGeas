# Phase 02 cost boundary

Phase 02 adds no recurring-cost infrastructure. It keeps the already-running `t3.medium` development host and its existing storage/network usage. The current bill remains the authoritative cost source; this evidence does not invent a numeric amount without billing access.

AWS Organizations, additional accounts, VPC/NAT, ECS, Atlas, Valkey, RabbitMQ, MSK, managed observability, staging, production, DR, and paid provider capabilities are outside the Phase 02 cost envelope and remain unprovisioned.

Before production activation, the owner must approve a consolidated current estimate based on measured workload, required capacity, data transfer, availability, provider tiers, and retention. The rollout ADR records the hard ceiling before any apply.
