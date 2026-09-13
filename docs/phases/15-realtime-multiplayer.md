# Phase 15 — Real-Time Multiplayer

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Clients provide intents; only the match service finalizes state and results.

## Mission

Deliver the reusable WebSocket gateway, authoritative 20 Hz match host, reconnect/checkpoint policy, real-time mechanics interface, SDK transport, Studio operations, and qualification capacity.

## Required reading and entry

Phase 14 must be accepted. Read its handoff and system architecture, runtime, API/events/jobs/timers, multiplayer, security, SRE, testing, and infrastructure contracts.

## Exact outputs

```text
apps/realtime-gateway/
apps/match-service/
packages/protocol/realtime/v1/*.proto
packages/domain/realtime/
packages/persistence/{valkey,mongodb}/realtime/
mechanics/realtime-session/
packages/sdk-*/realtime/
infrastructure/terraform/modules/{realtime-service,match-service}/
tests/{contract,integration,e2e,determinism,performance,security}/realtime/
docs/runbooks/{realtime-capacity,match-host-loss,websocket-drain,realtime-abuse}.md
```

## Tasks

- [ ] **P15-T01 — Protocol v1.** Define Protobuf handshake, welcome, input, ack, snapshot, delta, event, heartbeat, reconnect, close, and error messages. Specify frame size, compression, sequence, tick, MAC, compatibility, unknown field, and rate behavior. Generate bindings for TypeScript, C#, Kotlin, Swift, and Python.
- [ ] **P15-T02 — Realtime gateway.** Authenticate Supabase/session token, authorize roster, negotiate protocol/definition, enforce Cloudflare and application limits, verify MAC/sequence, maintain heartbeat, write expiring routing/presence, propagate trace IDs, proxy to match host, and drain during deploy. Depends on P15-T01.
- [ ] **P15-T03 — Match allocation and host.** Allocate one ECS task per match group, use committed seed, run fixed 20 Hz loop, accept bounded input lead, reject late/illegal input, publish 10 Hz snapshots plus immediate critical events, isolate CPU/memory, checkpoint, and create deterministic replay artifact. Depends on P15-T02 and Phase 14 match service.
- [ ] **P15-T04 — Reconnect and host failure.** Issue scoped resume tokens, acknowledge sequences, restore snapshot/input tail, expire reconnect, restore checkpoint when package supports it, otherwise cancel without rating loss and compensate once. Kill/restart cannot finalize twice. Depends on P15-T03.
- [ ] **P15-T05 — Realtime mechanics contract.** Release package schemas for tick, inputs, state, snapshot visibility, buffer, reconnect, checkpoint, result projection, analytics, migrations, simulator hooks, Studio controls, and SDK client base. Depends on P15-T03–T04.
- [ ] **P15-T06 — Extension proof.** Use `fixture_cards_realtime` and `fixture_td_realtime` to prove radically different packages use the same host and protocol without core dispatch edits. Depends on P15-T05 and Phase 13 packages.
- [ ] **P15-T07 — Competitive red team.** Attempt forged damage/currency/result/reward, input replay/reorder/flood, speed/clock manipulation, state inspection, session theft, reconnect duplication, definition mismatch, host impersonation, collusion/disconnect abuse, and direct-origin access. Depends on P15-T02–T06.
- [ ] **P15-T08 — Capacity qualification.** Run 100,000 concurrent sockets, 10,000 simultaneous matches, 20 Hz input, 10 Hz snapshot, p99 accepted-input processing at or below 50 ms, three-AZ placement, one-AZ loss, autoscaling, graceful drain, cost, and telemetry cardinality checks.

## Determinism and persistence rules

The match host uses logical tick and seeded RNG only. Renderer frame rate and network arrival time cannot alter legal result once input ordering is fixed. Valkey stores routing/presence only. MongoDB stores match metadata and final result; R2 stores compressed replay/checkpoints; progression/economy consume one signed result event.

## Gate and handoff

Run protocol compatibility, cross-SDK, deterministic replay, host-kill, AZ-loss, soak, security, resource-limit, and capacity suites plus `task phase:gate PHASE=15`. Handoff to Phase 16 provides no gameplay authority to AI; it lists only definition schemas, simulator APIs, governed analytics, operational views, package catalogs, and synthetic fixtures agents can use.
