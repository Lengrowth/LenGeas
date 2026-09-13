# Saves, Offline Play, and Synchronization

## Save envelope

Every save contains player ID, game ID, game version, definition digest, engine version, save schema version, module state versions, state version, canonical state digest, logical last-active time, server checkpoint, device ID, created/updated timestamps, and integrity metadata.

The server stores immutable save checkpoints and a current pointer. Clients store an encrypted local snapshot plus a journal of locally approved actions.

## Network mode behavior

| Mode | Authoritative execution |
|---|---|
| `offline` | Local runtime; server stores optional encrypted backup and marks state untrusted for competitive/cross-game value |
| `offline_first` | Local allowlisted actions plus journal; server reconciles on sync |
| `online_optional` | Local non-value actions; server required for purchases, entitlements, social, and cross-game rewards |
| `online_required` | Server executes all persistent mutations |
| `server_authoritative` | Server or match server executes every gameplay mutation |

## Offline action policy

An action can execute locally only when its published definition says `authority: local`, every effect stays in an offline namespace, rewards are marked locally reconcilable, and no purchase, entitlement, cross-game value, competitive rating, or scarce server-owned item is involved.

The client journal records sequence, input, prior digest, result digest, logical time, definition digest, engine version, seed, and device signature. Editing the snapshot without a matching journal fails integrity verification.

## Sync protocol

1. Client sends checkpoint ID, state version/digest, device sequence, definition digest, and compressed action journal.
2. Server authenticates device and validates size, sequence, timestamps, definition, signatures, and replay window.
3. Server replays the journal from the last accepted checkpoint with the server runtime.
4. Exact digest match accepts the journal and produces a new server checkpoint.
5. A mismatch applies the configured domain resolution policy or quarantines the sync.
6. Server returns accepted sequence, canonical snapshot/patch, new checkpoint, rejected actions with codes, and required definition/save migrations.

## Conflict policies

- Economy, inventory, entitlements, purchases, achievements, and cross-game rewards use transaction/action replay. Snapshot winner policies are forbidden.
- Cosmetic settings and non-authoritative preferences use latest valid server-received update.
- Story choices and progression use branch-aware domain merge only when the definition declares branches mergeable; otherwise the player selects one branch.
- Concurrent device action journals are ordered by server receipt per player. Conflicting non-commutative actions reject with a rebase response.

## Offline progress

The server clamps elapsed time to the definition's offline cap, subtracts suspicious clock movement, evaluates timers and generators in aggregate, and returns a transparent calculation receipt. The maximum offline cap in v1 is 30 days. Each game definition can set a lower cap.

## Save migrations

Migrations are pure functions from one schema version to the next. They are deterministic, idempotent at the orchestration layer, digest-verified, and covered by golden fixtures. The server migrates before action replay. Clients never invent migration output.

## Abuse handling

Signals include clock rollback, impossible journal rate, unknown seed, modified definition, invalid device signature, repeated rejected journal, value divergence, and device fan-out. The server accepts safe non-value state, quarantines disputed value, records a fraud signal, and returns a stable support reference. It never silently grants disputed value.
