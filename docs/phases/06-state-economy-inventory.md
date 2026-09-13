# Phase 06 — State, Economy, and Inventory

## Goal

Deliver durable player state and value integrity through transactional economy, inventory, purchases, and entitlements.

## Entry

Phase 05 is accepted.

## Tasks

- [ ] **P06-T01 — Implement partitioned player state.** Build profile, namespace documents, optimistic versions, limits, projections, and state patch responses. Evidence: concurrency and size tests.
- [ ] **P06-T02 — Implement double-entry ledger.** Create transaction headers, entries, system accounts, faucets, sinks, exchanges, balance projection, and compensations. Depends on P06-T01. Evidence: conservation property suite.
- [ ] **P06-T03 — Implement atomic economy actions.** Execute costs, grants, caps, overflow routes, multipliers, purchases, and exchanges with receipt/idempotency/outbox in MongoDB transactions. Depends on P06-T02, P05-T07. Evidence: atomicity and idempotency fault-injection report.
- [ ] **P06-T04 — Implement inventory.** Build containers, stacks, unique instances, equipment, ownership transfer policy, capacity, grant/consume, and item history through action plans. Depends on P06-T01–T03. Evidence: race and ownership tests.
- [ ] **P06-T05 — Implement entitlements and receipts.** Verify Apple/Google provider receipts, reconcile webhooks, grant permanent/consumable/subscription entitlements, process refunds, and prevent duplicate provider transactions. Depends on P06-T02–T04. Evidence: provider sandbox matrix.
- [ ] **P06-T06 — Implement cross-game delivery.** Create approved contract service, source event validation, target action, delivery limit, idempotency, and revocation records. Depends on P06-T03, P05-T07. Evidence: isolation and loop tests.
- [ ] **P06-T07 — Implement reconciliation.** Run receipt-ledger-balance-inventory-entitlement-cross-game checks, alert/quarantine mismatches, and produce repair proposals. Depends on P06-T02–T06. Evidence: injected-corruption drill.
- [ ] **P06-T08 — Attack value integrity.** Test negative balances, overflow, concurrency, repeated claims, exchange cycles, refund re-grants, journal replay, and cross-game loops. Depends on P06-T03–T07. Evidence: exploit report with zero unresolved high findings.

## Exit gate

One billion generated value operations reconcile with zero unexplained imbalance; duplicates and concurrency grant no extra value; purchase sandbox and cross-game isolation tests pass.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 05 handoff and data, runtime, API, sync, security, and testing contracts.

### Exact outputs

`packages/domain/{player_state,economy,inventory,entitlements,cross_game}/`; matching MongoDB repositories; action/effect/reward registrations; API routers; schemas for ledger/transactions/items/entitlements/purchases/transfers; reconciliation Celery tasks; Apple/Google provider adapters; support runbooks; and economy/inventory tests across all test layers.

Create the exact collections and indexes defined in `07-data-and-persistence.md`. Ledger entries are append-only, corrections are compensating transactions, and conserved assets balance to zero including named faucet/sink system accounts. Provider transaction ID is the permanent purchase key.

### Required scenarios

- Concurrent spend against one balance, duplicate grant/claim, partial multi-resource cost, overflow route loop, cap/clamp/reject, exchange cycle, and compensation.
- Stackable and unique items, capacity conflict, equip race, consume race, ownership transfer denial, and item-history rebuild.
- Apple/Google valid, invalid, pending, duplicate, delayed webhook, subscription renew/expire, refund, and chargeback.
- Cross-game approved/expired/revoked contract, duplicate source event, source-target isolation, delivery cap, and cyclic reward rejection.
- Inject balance/ledger, receipt/ledger, inventory/history, and entitlement/provider corruption; reconciliation detects and quarantines every mismatch.

The qualification generator runs one billion operations in partitioned CI/performance infrastructure and stores seed ranges, aggregate counts, and digest, not one billion raw records in Git.

### Handoff to Phase 07

Provide player-state repository API, ledger account/transaction schemas, item/entitlement handlers, reconciliation commands/metrics, provider sandbox configuration names, and cross-game delivery contract.
