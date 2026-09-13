# Multiplayer

## v1 services

LenGeas provides friends, blocks, parties, presence, lobbies, queues, matchmaking, ratings, leaderboards, match sessions, asynchronous turns, real-time inputs, reconnection, match results, rewards, history, moderation hooks, and replay inspection.

## Authority

The server owns queue eligibility, roster, seed, rules digest, time, legal inputs, state transitions, damage, score, result, rating, and rewards. Clients send signed intents with sequence numbers. Client simulation is prediction only.

## Match lifecycle

`created -> assembling -> ready_check -> active -> resolving -> completed -> archived`

Failure states are `cancelled`, `abandoned`, and `disputed`. Every transition is a persisted command with expected version and idempotency key.

## Matchmaking

A ticket contains game, mode, region, party, player IDs, rating and uncertainty, latency samples, definition digest, client protocol, cross-play flags, and creation time. The matcher uses expanding windows over rating, latency, and wait time. Parties are indivisible.

Ratings use Glicko-2 with game-mode-specific configuration. Rating updates execute only from signed completed match results and remain idempotent. Matchmaking configuration is versioned and experiment-aware.

## Realtime protocol

- WebSocket connections enter through Cloudflare and the AWS ALB to `realtime-gateway`.
- Binary messages use Protocol Buffers; the handshake and operational errors use JSON.
- Client inputs contain match ID, player ID, input sequence, client tick, action, payload, and session MAC.
- The match service runs a fixed 20 Hz authoritative tick for v1 real-time packages.
- State snapshots publish at 10 Hz; critical events publish immediately.
- Input lead, late-input rejection, reconnect window, and snapshot frequency are mode configuration bounded by platform limits.
- A match is assigned to one ECS task for its lifetime. Valkey stores routing and presence, while periodic checkpoints and final history persist to MongoDB/R2.

No seamless live migration occurs during a match in v1. Instance loss restores from the latest checkpoint when the package supports recovery; otherwise the match becomes `cancelled` and reward/rating policy compensates players.

## Asynchronous matches

Every turn validates expected turn number, actor, deadline, definition digest, and prior state digest. The server applies the turn and writes an immutable replay event. Deadline timers trigger default action or forfeit according to the mode definition.

## Result finalization

The match service signs a result record containing roster, rules digest, initial seed commitment, ordered input digest, final state digest, outcome, integrity flags, and server instance identity. The progression service consumes the result once, grants rewards, and applies rating changes in separate traceable transactions.

## Presence, friends, and parties

Valkey maintains expiring presence and party leases. MongoDB stores durable relationships, blocks, invitations, and party history. Block rules override invites and matchmaking. Presence exposes coarse states only and respects privacy settings.

## Leaderboards

Valkey sorted sets serve hot ranks; MongoDB stores submissions and periodic snapshots. Each score submission is derived from a server action or match result. Seasonal reset archives a signed snapshot before clearing the live projection.

## Abuse and moderation

The platform records invalid-input rate, sequence manipulation, impossible timing, disconnect abuse, collusion signals, and result disputes. Sanctions are scoped, time-bound, reasoned, appealable, and audited. Chat and voice are outside v1.

## Capacity and SLO

The production gate demonstrates 100,000 concurrent WebSocket connections across the region, 10,000 simultaneous 20 Hz matches, p99 accepted-input processing under 50 ms within the region, and recovery behavior under one-AZ loss. These are platform test loads, not promised tenant quotas.
