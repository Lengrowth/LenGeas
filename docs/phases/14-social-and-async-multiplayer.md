# Phase 14 — Social and Asynchronous Multiplayer

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Persistent rewards remain economy actions and match results remain server facts.

## Mission

Deliver friends, privacy, parties, presence, lobbies, queues, matchmaking, Glicko-2 ratings, leaderboards, asynchronous matches, results, rewards, history, disputes, and moderation hooks.

## Required reading and entry

Phase 13 must be accepted. Read its handoff and identity, API/events/jobs/timers, publishing, mechanics, multiplayer, security, persistence, and SRE documents.

## Exact outputs

```text
packages/domain/{social,party,presence,lobby,matchmaking,rating,match,leaderboard,moderation}/
packages/persistence/{mongodb,valkey}/multiplayer/
apps/api/app/{social,parties,lobbies,matchmaking,matches,leaderboards,moderation}/
apps/workers/event_projectors/multiplayer/
mechanics/async-multiplayer/
packages/schemas/api/v1/multiplayer/
tests/{unit,property,contract,integration,e2e,performance,security}/multiplayer/
docs/runbooks/{matchmaking,async-match-dispute,leaderboard-rebuild,presence-degradation}.md
```

## Tasks

- [ ] **P14-T01 — Social graph.** Implement request/accept/reject/remove/block/unblock, invite policy, privacy, limits, pagination, mutual counts, and moderation actions. Block overrides every invite and matchmaking relation.
- [ ] **P14-T02 — Presence and parties.** Implement expiring Valkey presence/party leases, durable party history, leader/member roles, invites, join/leave/kick, leader transfer, ready state, privacy, reconnect, and failover rebuild. Depends on P14-T01.
- [ ] **P14-T03 — Lobby and queue.** Implement lobby state/version, capacity, ready check, mode/region/protocol/definition lock, party admission, queue ticket, cancellation, timeout, operational pause, and audited removal. Depends on P14-T02.
- [ ] **P14-T04 — Matchmaking and rating.** Implement latency samples, expanding rating/latency/wait windows, party indivisibility, region selection, deterministic tie-break, Glicko-2 rating/uncertainty/volatility, config versions, experiment variant, and integrity hold. Depends on P14-T03.
- [ ] **P14-T05 — Async match.** Implement lifecycle, roster, definition/package locks, committed seed, turn actor/number/version, deadline timer, legal action, immutable event, snapshot, default/forfeit, completion, dispute, archive, and deterministic replay. Depends on P14-T03–T04.
- [ ] **P14-T06 — Result and reward.** Sign result with roster/rules/seed/input/final-state digests, finalize once, emit fact, grant through economy, update rating, handle cancellation/dispute compensation, and expose history. Depends on P14-T04–T05.
- [ ] **P14-T07 — Leaderboards.** Accept only server-derived scores, serve Valkey sorted sets, persist submissions, tie-break deterministically, paginate, snapshot season with signature, reset, rebuild, and enforce privacy. Depends on P14-T06.
- [ ] **P14-T08 — Package and Studio/SDK integration.** Release async-multiplayer package with schemas, actions, events, timers, migrations, simulator strategies, Studio controls, SDKs, analytics, and runbooks.

## Required hostile scenarios

Cross-studio invite, blocked-user party join, party split, duplicate queue ticket, stale ready check, rating smurf/collusion fixture, timeout race with submitted turn, forged turn actor, changed definition, duplicate result, reward granted before final result, leaderboard spoof, season reset failure, Valkey loss, MSK duplicate, and Atlas transient transaction error.

## Gate and handoff

Run property tests for Glicko-2 bounds and deterministic matching, 100,000 queued tickets, 1 million async matches, failover/rebuild, authorization/abuse, replay, ledger reconciliation, and `task phase:gate PHASE=14`. Handoff to Phase 15 provides match lifecycle interfaces, signed result format, routing/presence keys, session allocation hook, rating/reward contracts, SDK types, and operational limits.
