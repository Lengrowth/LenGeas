# Platform Invariant Review Log

## Review state

- Phase task: `P00-T02`
- Status: `accepted`
- Source: `docs/01-principles-and-invariants.md`
- Decision owner: sole developer / repository owner
- Current staffing model: one developer, the repository owner, covers all listed responsibility roles. No separate reviewers, signatures, or meetings are required.

## Invariant disposition

| ID | Invariant | Owner role | Verification baseline | State |
|---|---|---|---|---|
| INV-01 | Backend is authoritative for authenticated online state, economy value, inventory, entitlements, published definitions, competitive results, and cross-game rewards. | Architecture owner | authorization, ledger, and replay suites | accepted |
| INV-02 | Clients send intent and never authoritative resulting balances, rewards, damage, entitlements, ratings, or match outcomes. | Game Systems owner | forged-result negative tests | accepted |
| INV-03 | Published definitions are immutable and content-addressed; corrections create a new version. | Definition owner | publish immutability and digest tests | accepted |
| INV-04 | Every state mutation runs through a named action and produces an auditable mutation record. | Runtime owner | action receipt and audit tests | accepted |
| INV-05 | Every value transfer runs in one economy transaction with balanced ledger entries and an idempotency key. | Data owner | ledger reconciliation and duplicate tests | accepted |
| INV-06 | Runtime execution is deterministic for the declared execution tuple. | Runtime owner | cross-platform replay suite | accepted |
| INV-07 | Runtime logic receives logical UTC time and does not read wall-clock time directly. | Runtime owner | clock isolation tests | accepted |
| INV-08 | Runtime logic uses only seeded random sources. | Runtime owner | seed and unseeded-RNG scans | accepted |
| INV-09 | Formulas and conditions use the bounded LenGeas expression AST; arbitrary code and `eval` are forbidden. | Security owner | formula resource-exhaustion and code-boundary tests | accepted |
| INV-10 | Authoritative state and money math uses integers or fixed-precision decimals; IEEE-754 floating point is forbidden. | Data owner | numeric conformance tests | accepted |
| INV-11 | Persisted documents carry `studio_id` and appropriate `game_id`; authorization filters both before access. | Identity owner | tenant-escape suite | accepted |
| INV-12 | Cross-game access requires a published contract naming source, target, data, purpose, and reward mapping. | Identity owner | cross-game contract tests | accepted |
| INV-13 | Modules read and write only manifest-declared state namespaces. | Package owner | module isolation tests | accepted |
| INV-14 | Domain events are past-tense facts; consumers do not mutate another domain's collection directly. | Eventing owner | event and repository boundary tests | accepted |
| INV-15 | External delivery is at least once and consumers are idempotent. | Eventing owner | duplicate delivery tests | accepted |
| INV-16 | API, event, save, definition, and package versions evolve independently under compatibility rules. | Architecture owner | compatibility matrix and migration tests | accepted |
| INV-17 | Humans and AI agents use the same public Definition API and validation/publishing pipeline. | Studio owner | identical API audit | accepted |
| INV-18 | AI output begins as a draft and cannot approve its own publication. | AI Control Plane owner | self-approval and tool-scope tests | accepted |
| INV-19 | PII is stored outside game state and never emitted in analytics payloads. | Security owner | privacy and analytics redaction tests | accepted |
| INV-20 | Logs, traces, metrics, and audit records contain no credentials or raw authentication tokens. | SRE owner | secret scanning and telemetry tests | accepted |

## Owner acceptance record

| Responsibility area | Decision owner | Approval reference | UTC | Decision |
|---|---|---|---|---|
| Architecture owner | sole developer / repository owner | direct owner approval | 2026-09-13 | accepted |
| Security owner | sole developer / repository owner | direct owner approval | 2026-09-13 | accepted |
| Data owner | sole developer / repository owner | direct owner approval | 2026-09-13 | accepted |
| Game Systems owner | sole developer / repository owner | direct owner approval | 2026-09-13 | accepted |

## Decision

`accepted`

No invariant was weakened or reinterpreted. The repository owner accepted the full list directly for the one-person company.
