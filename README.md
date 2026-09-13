# LenGeas

LenGeas is a universal, data-driven game systems platform. It provides shared systems, optional mechanics packages, and versioned content definitions from which focused games are built. LenGeas is not a single game and it does not combine unrelated mechanics into one runtime.

This repository is documentation-only until Phase 00 is approved. No product code belongs here before that gate.

## Delivery team model

The current LenGeas delivery team is one developer: the repository owner. The owner holds every responsibility role, may implement and review the same change, and is the sole approval authority for every delivery phase and release. Role IDs remain responsibility and traceability labels; they do not require separate people, meetings, signatures, CODEOWNER reviews, or approval counts. Automated verification and stored evidence remain mandatory. AI agents may prepare and review work, but they cannot record the owner's approval.

## Canonical documentation

- [Documentation map](docs/README.md)
- [Product charter and v1 scope](docs/00-product-charter.md)
- [Architecture and boundaries](docs/02-system-architecture.md)
- [Technology standard](docs/03-technology-standard.md)
- [Game Definition Schema v0.1](docs/05-game-definition-schema-v0.1.md)
- [Delivery plan](docs/phases/README.md)
- [Platform completion contract](docs/22-platform-completion-contract.md)
- [Traceability matrix](docs/23-traceability-matrix.md)
- [Assets, localization, and notifications](docs/24-assets-localization-notifications.md)

## Non-negotiable release rule

No first-party game starts before every required phase is complete and the Platform Completion Review records `PASS`. Test fixtures, protocol probes, synthetic definitions, and conformance scenarios are platform verification artifacts; they are not games.

## Normative language

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` use RFC 2119 meanings. Architecture and phase documents use `MUST` for required v1 work. `MAY` appears only in extension contracts that explicitly permit a game-definition author to choose behavior.

## Change control

Architecture changes require an accepted Architecture Decision Record (ADR), updated affected documents, updated traceability entries, and approval from the platform technical lead. A phase cannot close against undocumented behavior.
