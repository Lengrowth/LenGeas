# State, Economy, and Inventory API v1

Phase 06 exposes an injectable authenticated router factory at
`apps/api/app/state_economy_api.py`. Production composition must supply the
Phase 03 trusted identity provider and a durable Mongo repository; request
fields never select the studio scope. The router provides namespace
projection/patch and atomic economy action endpoints.

## Player state

- `GET /api/v1/games/{game_id}/players/{player_id}/state?game_profile_id=...`
- `PATCH /api/v1/games/{game_id}/players/{player_id}/state/{namespace_id}`
- Patch body: `game_profile_id`, `expected_version`, and a JSON merge patch.
- Responses include prior and next namespace versions, the applied patch,
  canonical state digest, and update timestamp. Stale versions return 409.
- Per namespace patch limit is 256 KiB; stored namespace documents are limited
  to 6 MiB.

## Economy

- `POST /api/v1/games/{game_id}/players/{player_id}/economy/actions`
- Requires `Idempotency-Key`, action ID, expected state version, and action
  payload. The injected trusted server-side action resolver computes the state
  patch, costs, grants, integer multipliers, caps/overflow policy, and frozen
  definition digest. Client-provided reward amounts are rejected.
- A successful durable response contains receipt and transaction IDs, committed
  status, new state version, projected balances, and outbox event IDs.
- Ledger transactions are append-only and conserve each asset. Corrections use
  `MongoEconomyRepository.compensate`; stored entries are never rewritten.

## Persistence and support

Mongo repositories use only the documented `player_profiles`, `player_states`,
`inventories`, `economy_ledger`, `action_receipts`, `idempotency_records`,
`entitlements`, `outbox_events`, `game_blueprints`, and `audit_logs` collections.
Index setup methods are explicit and must run through the repository migration
process before traffic is enabled. See
`docs/runbooks/economy-inventory-support.md` for receipt, refund, quarantine,
and repair-proposal handling.
