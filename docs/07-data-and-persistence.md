# Data and Persistence

## Storage ownership

| Store | Durable authority | Contents |
|---|---|---|
| MongoDB Atlas | Yes | identities, studios, games, definitions metadata, player profiles/state, ledgers, saves, matches, experiments, outbox, audit indexes |
| Cloudflare R2 | Yes | definition bundles, assets, simulation results, analytics lake, signed exports, backup exports |
| Amazon MSK | Bounded retention | domain event stream and replay window |
| Amazon MQ | Until acknowledged | Celery task delivery |
| ElastiCache for Valkey | No | cache, leases, rate counters, presence, queue indexes, leaderboard projections |

## MongoDB tenancy

Every tenant-owned document begins with `studio_id`. Game-owned documents also contain `game_id`. Player-game documents contain `player_id` and `game_profile_id`. Repository constructors require a scope object; unscoped collection access is private to migrations and audited support tooling.

## Core collections

`accounts`, `studio_players`, `player_identities`, `studios`, `studio_memberships`, `games`, `game_blueprints`, `definition_versions`, `definition_channels`, `module_releases`, `player_profiles`, `player_states`, `inventories`, `economy_ledger`, `action_receipts`, `idempotency_records`, `saves`, `save_migrations`, `timers`, `quests`, `achievements`, `entitlements`, `experiments`, `experiment_assignments`, `matches`, `match_events`, `leaderboard_snapshots`, `outbox_events`, `audit_logs`, and `agent_runs`.

Analytics event bodies do not use MongoDB as their long-term store. They flow to partitioned Parquet files in R2.

## Player state partitioning

- `player_profiles` stores low-frequency identity within a game and the pinned definition.
- `player_states` stores module namespaces as bounded documents. Each namespace is one document keyed by player, game, and namespace.
- `inventories` partitions items by inventory container.
- `economy_ledger` is append-only and is not embedded in player state.
- `matches` and `match_events` are separate from persistent progression.

No MongoDB document can exceed 8 MiB in normal operation. A 6 MiB alert threshold creates an operator event.

## Concurrency

Authoritative mutable documents contain an integer `state_version`. Updates match the expected version and increment it once. Multi-document value changes use MongoDB transactions. Long external calls never occur inside a transaction.

## Economy ledger

Every transaction has a header and at least two entries. Each entry contains account, asset/resource, signed amount, balance after, reason, source, definition digest, actor, and timestamps. The sum of entries for a conserved asset is zero. Faucets and sinks post against named system accounts.

The ledger is append-only. Corrections use compensating transactions. Daily reconciliation verifies receipt-to-ledger, ledger-to-balance, entitlement-to-purchase, and cross-game transfer invariants.

## Index policy

- Every query used by an API or worker has a reviewed supporting index.
- Unique indexes enforce stable IDs, identity-provider links, definition versions, action idempotency scope, and event delivery keys.
- TTL indexes delete expired idempotency, sessions, task results, leases, and transient matches according to retention policy.
- Index creation uses reviewed migrations and production-safe rollout.

## Retention

| Data | Retention |
|---|---|
| Economy ledger and entitlements | 7 years |
| Audit log | 7 years in immutable export plus searchable 400 days |
| Published definition bundles | Indefinite |
| Raw analytics | 25 months |
| Match events | 13 months; longer for disputes under legal hold |
| Action receipts | 13 months |
| Idempotency records | 30 days; permanent business key for purchase fulfillment |
| Guest identities with no activity | 13 months |
| Deleted-account tombstones | 30 days except required financial/legal records |

## Backup and restore

Atlas continuous backup and point-in-time recovery are enabled in staging and production. R2 buckets use object versioning. Terraform state uses S3 versioning, KMS encryption, and native lockfiles. Quarterly restore drills create isolated targets and verify counts, digests, indexes, and sampled action histories.

## Migrations

Database migrations are ordered, idempotent, resumable, observable, and backward-compatible with the currently deployed application. Expand-and-contract is mandatory. Destructive cleanup occurs only after the old application version is removed, rollback expires, backup verification passes, and a separate approved task executes.
