# ADR-0002 — MongoDB Atlas document storage

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Data owner; SRE owner
- Supersedes: none
- Superseded by: none

## Context

LenGeas stores tenant-scoped definitions, player state, ledgers, identity, matches, outbox records, and audit indexes. The store needs document modeling, transactions for value changes, indexes, backups, PrivateLink, and regional restore.

## Decision

Use dedicated MongoDB Atlas clusters on AWS with private endpoints over AWS PrivateLink. MongoDB owns canonical durable documents and ledgers; R2 owns object artifacts. Repository constructors require an authorization scope and service boundaries own persistence access.

## Consequences

The choice fits document-shaped versioned state and transaction boundaries. It introduces Atlas cost, driver/version coupling, document-size and index discipline, and restore rehearsal obligations.

## Rejected designs

- Shared relational primary store: rejected because the baseline document and package contracts select MongoDB Atlas.
- Valkey as durable state: rejected because cache and leases cannot be the only durable copy of value.

## Validation

Transaction, index, tenant-scope, document-size, backup, point-in-time restore, and cross-region recovery tests are required before production rollout.

## Rollout and reversal

Provision isolated environments through Terraform, migrate with expand-and-contract procedures, and verify counts and digests. Reversal uses the prior compatible application and restore point; a store replacement requires an accepted superseding ADR.
