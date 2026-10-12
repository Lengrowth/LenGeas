# Phase 06 implementation decisions

- State partitions use one bounded `player_states` document per player, game,
  and namespace. Optimistic writes increment the namespace version.
- Economy transaction headers and immutable entries share the documented
  `economy_ledger` collection with separately tagged mutable balance projection
  documents. Each conserved asset balances to zero through named system
  accounts. Corrections append compensating transactions.
- Action receipts, permanent provider transaction keys, and outbox events are
  committed with state/value changes in MongoDB transactions. Provider
  transaction identifiers have no TTL.
- Inventory state is container-scoped in `inventories`; item history is
  append-only in `audit_logs`. Cross-game inventory transfer is denied; approved
  cross-game rewards use contracts embedded in `game_blueprints` and durable
  delivery receipts.
- Reconciliation quarantines mismatches, emits alerts, and writes
  owner-reviewed proposals; it never silently repairs value.
- Local evidence uses deterministic in-memory and provider fixture adapters.
  External Mongo/provider/hosted qualification is called out in blockers and
  is not represented as completed.
