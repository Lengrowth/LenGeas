# Phase 06 handoff

## Review status

Phase 06 is `in_review`. No owner acceptance is recorded. Local domain,
adapter-contract, API boundary, security, and bounded qualification checks are
documented in this evidence bundle. The billion-operation hosted run, MongoDB
transaction integration, real provider sandboxes, and Celery broker check are
still open risks. See `blockers.md`.

## Phase 07 interfaces

- `MongoPlayerStateRepository` stores one versioned document per
  studio/game/player/namespace and provides `read`, optimistic `patch`, and
  namespace `project`. `player_profiles` holds low-frequency profile data.
- `MongoEconomyRepository.execute_action` atomically updates the `economy`
  namespace, append-only transaction record, account projections, action
  receipt, scoped idempotency response, and outbox event. Entry amounts are
  signed int64 and must sum to zero per asset. Correct mistakes with a
  compensating transaction.
- `economy_action_from_runtime_plan` translates trusted Phase 05 resource costs
  and resource rewards into a Phase 06 `EconomyAction`; direct state effects
  and item rewards are rejected until their atomic domain handlers are supplied.
- `MongoInventoryRepository` stores per-container stacks, unique instances,
  equipment, optimistic state version, idempotency snapshots, and immutable
  item history. Same-game transfers run in one Mongo transaction; cross-game
  inventory transfers are denied.
- `MongoEconomyRepository.fulfill_purchase` accepts only an already verified
  `VerifiedPurchase`; it permanently keys by `(provider,
  provider_transaction_id)`. Refund/chargeback revocation appends an outbox
  event without deleting purchase or entitlement history.
- Apple verification adapter constructor inputs are server API base URL,
  bearer-token callback, and trusted root PEM chain. Suggested secret names for
  deployment: `APPLE_SERVER_API_BASE_URL`, `APPLE_SERVER_API_TOKEN`,
  `APPLE_TRUSTED_ROOTS_PEM`, and `APPLE_BUNDLE_ID`.
- Google verification adapter inputs are Play API base URL, access-token
  callback, Pub/Sub audience, and accepted OIDC issuer. Suggested secret names:
  `GOOGLE_PLAY_API_BASE_URL`, `GOOGLE_PLAY_ACCESS_TOKEN`,
  `GOOGLE_PUBSUB_AUDIENCE`, and `GOOGLE_PUBSUB_ISSUER`.
- Reconciliation is exposed as the Celery task
  `lengeas.reconciliation.run` on the `maintenance` queue. It writes findings
  to `audit_logs`, alerts to `outbox_events`, quarantine flags to affected
  documents, and review-only repair proposals.
- Cross-game approvals are embedded in `game_blueprints`; the source event,
  delivery limit, target action, idempotency key, durable receipt, and outbox
  record are enforced by `MongoCrossGameRepository`.

## API

The `create_state_economy_router` factory exposes namespace state projection and
patch plus atomic economy action routes. Production composition must provide
the Phase 03 trusted principal callback and Mongo repositories. The request
cannot choose its tenant. API contract details are in
`docs/reference/state-economy-inventory-v1.md`.

## Persistence ownership

Only the documented collections are used: `player_profiles`, `player_states`,
`inventories`, `economy_ledger`, `action_receipts`, `idempotency_records`,
`entitlements`, `outbox_events`, `game_blueprints`, and `audit_logs`. No new
collection is introduced. Explicit repository index definitions are named in
the Mongo adapters and use permanent provider transaction uniqueness.

## Commit reference

The Phase 06 implementation candidate is committed on main as `053a73e`. The evidence-manifest refresh is recorded separately so the manifest can hash the committed implementation and evidence artifacts.
