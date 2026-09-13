# Delivery Phases

## Execution rule

Phases execute in numeric order. Work inside a phase can run concurrently only when task dependencies permit it. A later phase can begin discovery, but it cannot merge implementation that depends on an unaccepted prior gate. Every completed task links evidence using `../templates/task-record.md`.

Every implementing agent must follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md) and begin from the [phase-agent prompt](../templates/phase-agent-prompt.md). A human reviewer uses the [phase review template](../templates/phase-review.md); an implementing agent cannot accept its own phase.

```text
00 Charter
  -> 01 Engineering foundation
  -> 02 Cloud foundation
  -> 03 Identity and tenancy
  -> 04 Definition schema
  -> 05 Runtime primitives
  -> 06 State, economy, inventory
  -> 07 Progression and SDKs
  -> 08 Registry, publishing, LiveOps
  -> 09 Saves and offline sync
  -> 10 Events, jobs, timers, analytics
  -> 11 Simulation, experiments, monetization
  -> 12 Game Studio
  -> 13 Solo mechanics packages
  -> 14 Social and async multiplayer
  -> 15 Real-time multiplayer
  -> 16 AI agent control plane
  -> 17 Production qualification and completion
```

## Phase index

- [Phase 00 — Charter and architecture lock](00-charter-and-architecture-lock.md)
- [Phase 01 — Engineering foundation](01-engineering-foundation.md)
- [Phase 02 — Cloud foundation](02-cloud-foundation.md)
- [Phase 03 — Identity, tenancy, authorization](03-identity-tenancy-authorization.md)
- [Phase 04 — Definition Schema v0.1](04-definition-schema.md)
- [Phase 05 — Runtime primitives](05-runtime-primitives.md)
- [Phase 06 — State, economy, inventory](06-state-economy-inventory.md)
- [Phase 07 — Progression and SDKs](07-progression-and-sdks.md)
- [Phase 08 — Registry, publishing, LiveOps](08-registry-publishing-liveops.md)
- [Phase 09 — Saves and offline sync](09-saves-and-offline-sync.md)
- [Phase 10 — Events, jobs, timers, analytics](10-events-jobs-timers-analytics.md)
- [Phase 11 — Simulation, experiments, monetization](11-simulation-experiments-monetization.md)
- [Phase 12 — Game Studio](12-game-studio.md)
- [Phase 13 — Solo mechanics packages](13-solo-mechanics-packages.md)
- [Phase 14 — Social and async multiplayer](14-social-and-async-multiplayer.md)
- [Phase 15 — Real-time multiplayer](15-realtime-multiplayer.md)
- [Phase 16 — AI agent control plane](16-ai-agent-control-plane.md)
- [Phase 17 — Production qualification](17-production-qualification.md)

## Status values

`not_started`, `in_progress`, `blocked`, `in_review`, and `accepted` are the only phase statuses. A phase is `accepted` only after its exit gate is signed.

## No-game checkpoint

Every phase review confirms that no first-party game, game renderer, or release content has entered the repository. Synthetic conformance definitions are named `fixture_*` and remain under tests.
