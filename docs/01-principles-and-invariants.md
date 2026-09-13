# Principles and Invariants

## Platform invariants

1. The backend is authoritative for authenticated online state, economy value, inventory, entitlements, published definitions, competitive results, and cross-game rewards.
2. A client sends intent. It never sends an authoritative resulting balance, reward, damage value, entitlement, rating, or match outcome.
3. Published definitions are immutable and content-addressed. A correction creates a new version.
4. Every state mutation runs through a named action and produces an auditable mutation record.
5. Every value transfer runs in one economy transaction with balanced ledger entries and an idempotency key.
6. Runtime execution is deterministic for a fixed engine version, definition digest, initial state, seed, logical time, and ordered input stream.
7. Runtime logic never reads wall-clock time directly. The caller supplies logical UTC time.
8. Runtime logic never uses an unseeded random source.
9. Definition formulas and conditions use the bounded LenGeas expression AST. Arbitrary code and `eval` are forbidden.
10. State and money math uses integers or fixed-precision decimals. IEEE-754 floating point is forbidden for authoritative values.
11. Every persisted document carries `studio_id` and the appropriate `game_id`; authorization filters both before access.
12. Cross-game access is denied unless a published cross-game contract names the source, target, data, purpose, and reward mapping.
13. A module reads and writes only state namespaces declared in its manifest.
14. Domain events are facts in past tense. Consumers do not mutate another domain's collection directly.
15. External delivery is at least once. Consumers are idempotent.
16. API, event, save, definition, and package versions change independently and follow documented compatibility rules.
17. Humans and AI agents use the same public Definition API and the same validation and publishing pipeline.
18. AI output always begins as a draft and cannot approve its own publication.
19. Personally identifiable information is stored outside game state and is never emitted in analytics payloads.
20. Logs, traces, metrics, and audit records never contain credentials or raw authentication tokens.

## Design rules

- Prefer a small explicit primitive over an all-purpose base class.
- Add an abstraction only after two concrete platform capabilities require the same contract.
- Keep domain logic free of FastAPI, MongoDB, Redis, broker, and Cloudflare imports.
- Keep orchestration separate from pure rule evaluation.
- Store references as stable IDs, not display names or array positions.
- Reject unknown fields in published schemas. Draft tooling preserves unknown extension fields only inside a namespaced `extensions` object.
- Return machine-readable error codes with human-readable detail.
- Make a failure visible; do not silently repair authoritative value.

## Determinism contract

The canonical execution tuple is:

`engine_version + definition_digest + state_version + action_id + action_payload + logical_time + rng_seed`

The runtime serializes results through canonical JSON: UTF-8, lexicographically sorted object keys, normalized decimal strings, UTC timestamps with `Z`, and no insignificant whitespace. SHA-256 of canonical bytes is the state or definition digest.

## Module isolation contract

Every module manifest declares:

- module ID and semantic version;
- compatible engine range;
- required modules and incompatible modules;
- configuration schema reference;
- owned state namespaces;
- actions, events, conditions, effects, timers, analytics, and migrations it registers;
- required permissions and resource budgets.

Module dependency cycles are invalid. Module initialization order is the topological dependency order with module ID as the stable tie-breaker.

## Documentation invariant

Every mandatory requirement has a stable requirement ID and maps to at least one phase task and one verification gate in the traceability matrix.
