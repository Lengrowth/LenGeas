# Product Charter and v1 Scope

## Mission

LenGeas enables teams and approved AI agents to define, validate, simulate, publish, operate, and analyze multiple focused games through one secure platform. Games share infrastructure and universal primitives while loading only the systems and mechanics declared by their blueprint.

## Delivery team model

The current internal delivery team is one developer: the repository owner. In this charter, “teams” refers to the studios and organizations that may use LenGeas, not to the internal delivery staffing model. The owner holds every responsibility role and is the sole approval authority for all phases, releases, financial corrections, infrastructure changes, and definition publications. No second person, committee, meeting, handwritten or cryptographic signature, CODEOWNER review, or minimum approval count is required. Automated gates, audit records, explicit owner decisions, and the rule that an AI cannot approve its own output remain binding.

## Product model

LenGeas separates three layers:

| Layer | Meaning | Example |
|---|---|---|
| System | Reusable platform capability | Economy transactions |
| Mechanic | Optional rules package | Idle production |
| Content | Versioned game-owned data | Mining Robot produces 10 iron per second |

No content object can introduce executable code. No mechanic can bypass core transactions, authorization, audit, event, version, or determinism contracts.

## v1 completion boundary

LenGeas v1 is complete only when all of the following operate in production and pass the gates in `22-platform-completion-contract.md`:

- Multi-tenant studios, users, roles, service accounts, universal players, guests, identity linking, and guest merge.
- Game blueprints, immutable definition versions, draft validation, staged publishing, rollback, and environment promotion.
- Entity, state, resource, condition, action, cost, effect, reward, relationship, event, timer, progression, quest, achievement, inventory, entitlement, formula, and localization primitives.
- Transactional economy operations with idempotency, ledgers, reconciliation, audit history, and fraud signals.
- Versioned saves, deterministic migrations, offline-first synchronization, conflict policies, and suspicious-state quarantine.
- Headless simulation, synthetic player profiles, balance assertions, deterministic experiment allocation, and centralized analytics.
- LiveOps, remote configuration allowlists, seasons, offers, purchases, ads, and server-side entitlements.
- Game Studio authoring for every v1 schema, visual progression and economy tooling, simulation controls, approval, publishing, audit, support, and operational views.
- Mechanics packages for idle, prestige, story/dialogue/choice, RPG/progression/combat, cards, merge, tower defense, crafting, and management simulation.
- Platform services for friends, parties, presence, lobbies, matchmaking, ratings, leaderboards, asynchronous matches, session-based real-time matches, rewards, and match history.
- AI Director plus design, story, economy, balance, QA, LiveOps, and analytics agents operating exclusively through the same definition APIs used by the Studio.
- Production infrastructure, least privilege, supply-chain security, observability, incident response, backup restore, regional disaster recovery, capacity tests, and cost controls.
- Client SDKs for TypeScript, C#, Kotlin, and Swift, plus a server SDK for Python. These SDKs expose platform contracts; they do not provide rendering engines.
- Governed asset ingestion and delivery, localization catalogs and fallback, in-game inbox, transactional email, mobile push, and web push.

## Supported product classes

The v1 contracts support idle/incremental, tower defense, choice-driven story, RPG progression, card battler, merge, management/simulation, asynchronous multiplayer, turn-based multiplayer, and small session-based real-time strategy games.

## Explicit v1 exclusions

- A first-party game, playable content catalog, art pipeline, or game client renderer.
- An FPS physics, rollback-netcode, anti-cheat kernel driver, voice-chat, or large-world MMO engine.
- Public self-service SaaS billing for external studios.
- Arbitrary user code, arbitrary scripts, or AI-authored production code in definitions.
- Cryptocurrency, tradable assets, gambling, or cash-out economies.
- A public mechanics marketplace. The package registry is internal in v1.

Exclusions do not weaken platform completion. They mark product categories that require a later charter and ADR.

## Users

- Platform operator: deploys, secures, observes, and supports LenGeas.
- Studio owner: controls a tenant and its games.
- Developer: integrates clients, SDKs, modules, and services.
- Designer/writer: authors definitions without changing engine code.
- Analyst: queries governed analytics and experiments.
- Support agent: inspects player history through redacted, audited tools.
- AI agent: proposes schema-conforming draft changes with scoped credentials.
- Player: owns one Studio Player identity and isolated per-game profiles.

## Success metrics

| Metric | v1 acceptance |
|---|---|
| Definition reproducibility | Same definition digest, seed, input state, and action stream produce byte-equivalent canonical output |
| Cross-game isolation | Automated authorization suite proves zero undeclared reads or writes across game boundaries |
| Content agility | A definition-only change reaches staging without an API image rebuild |
| Runtime reuse | Every v1 mechanics package uses core action, condition, effect, event, timer, and transaction interfaces |
| Availability | Production API monthly SLO is 99.95%; Studio monthly SLO is 99.9% |
| Recovery | Regional RTO is 4 hours; persistent-data RPO is 15 minutes |
| Performance | Public API p95 is at most 250 ms and p99 is at most 750 ms, excluding declared long-running jobs |
| Integrity | Duplicate execution under the idempotency test suite grants no duplicate value |
| Operability | Every Sev-1 alert links to an exercised runbook and named owner |
| Extensibility | A contract-test module can register without editing core domain implementation |

## Release policy

The platform technical lead signs the v1 completion record only after every Phase 00–17 exit gate passes. An exception cannot convert a failed mandatory gate into platform completion.
