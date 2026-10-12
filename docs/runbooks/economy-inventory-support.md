# Economy and Inventory Support Runbook

## Purchase lookup and refund

1. Search `action_receipts` by receipt ID or by provider plus
   `provider_transaction_id` within the supplied studio/game/player scope.
2. Verify the durable `idempotency_records` provider key and matching
   entitlement. Provider transaction IDs are permanent business keys; do not
   delete or expire these records.
3. Validate refund or chargeback state with the provider adapter. Call
   `MongoEconomyRepository.revoke_purchase` with `refund`, `chargeback`, or
   `provider_revocation`; the transaction marks the entitlement revoked and
   adds an outbox event. Do not grant a replacement based on a replayed receipt.

## Inventory discrepancy

1. Run the `lengeas.reconciliation.run` Celery task for the affected studio.
2. Inspect `integrity.finding.v1` audit records, the associated pending outbox
   alert, and the quarantined entity.
3. Rebuild the current container from immutable
   `inventory.item_history.v1` records and compare counts, unique instance IDs,
   equipment references, capacity, and state version.
4. Reconciliation repair proposals are review-only. An authorized owner must
   approve any compensating economy transaction or inventory repair. Never edit
   ledger transactions or silently restore an entitlement.

## Reconciliation response

The reconciliation task compares receipts, balanced ledger entries and
projections, inventory containers and history, entitlements and provider keys,
and cross-game delivery records against approved contracts. High-severity
findings are quarantined and emitted to the outbox. Investigate duplicate
provider IDs, unapproved transfers, or mismatched balances before clearing a
quarantine. Retain the finding, proposal, approval, and repair transaction IDs
in the support case.

## Unavailable systems

Production recovery requires MongoDB transaction support, the maintenance
RabbitMQ queue, configured Apple/Google credentials, and the trusted API
principal/repository composition. Local Phase 06 validation uses deterministic
domain adapters and provider HTTP/JWS fixtures; it does not emulate hosted
provider approval or Mongo commit behavior.
