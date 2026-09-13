# Runtime and Rules

## Runtime layers

1. Pure evaluator: conditions, formulas, action plans, effects, rewards, timers, and deterministic event creation.
2. Application orchestrator: authorization, idempotency, definition selection, state loading, transaction boundaries, and retries.
3. Adapters: MongoDB, Valkey, RabbitMQ, MSK, R2, HTTP, and WebSocket.

The pure evaluator has no network, database, filesystem, environment-variable, or wall-clock access.

## Action lifecycle

1. Parse and schema-validate the action envelope.
2. Authenticate actor and authorize studio, game, player, profile, and action.
3. Reserve the idempotency key for the actor and action class.
4. Resolve the environment's active definition or the player's pinned definition.
5. Load state at an expected optimistic version.
6. Construct execution context with logical time, deterministic seed, locale, experiment assignments, and module registry.
7. Evaluate preconditions without mutation.
8. Build costs, effects, rewards, timers, and events as an immutable execution plan.
9. Validate the plan against resource limits and namespace permissions.
10. Commit plan, ledger, new state version, action receipt, and outbox events in a MongoDB transaction.
11. Cache the action receipt and return it.
12. Publish outbox events asynchronously.

On optimistic conflict, the orchestrator reloads and retries at most two times. A third conflict returns `state_conflict` without partial mutation.

## State paths

Paths use registered tokens, not arbitrary JSONPath. The registry maps tokens such as `player.level`, `resource.gold.balance`, and `quest.intro.status` to typed accessors. Each module declares readable and writable tokens. Publication resolves tokens and rejects unresolved or unauthorized paths.

## Condition evaluation

- Evaluation is pure and side-effect free.
- `all` and `any` evaluate children in stored order and return a structured explanation tree.
- Missing state is an error unless the operator explicitly accepts absence.
- Comparisons reject incompatible types.
- A failed condition is a domain denial, not a server error.

## Effects and rewards

Effects execute in plan order. Rewards expand into effects through registered reward handlers before commit. A handler cannot issue a nested transaction or call an external service. External fulfillment, including purchase verification and cross-game delivery, writes a pending record and completes through an idempotent workflow.

## Events

Events contain facts from a committed change. The evaluator assigns a deterministic local ordinal; the application assigns UUIDv7 event IDs at commit. No consumer can alter the original transaction. Follow-up work executes a new named action with causation and correlation IDs.

## Timers and logical time

Timer state stores start, due, authority, definition version, payload, status, and firing idempotency key. The scheduler claims due timers with leases and invokes the configured action. Offline catch-up uses the same timer evaluator with a bounded interval and stored last-evaluated time.

## Package registry

The engine loads only blueprint-declared packages. Registration freezes before the first action. Duplicate action/effect/event/state registrations fail startup. Package code is trusted platform code, signed and released through CI; definition content remains untrusted data.

## Resource budgets

Each action enforces:

- maximum condition nodes: 256;
- maximum formula operations: 512;
- maximum effects after expansion: 128;
- maximum emitted events: 64;
- maximum state patch size: 256 KiB;
- maximum execution time in pure evaluator: 50 ms at the reference CPU;
- maximum transaction duration: 500 ms before abort.

Package-specific lower budgets are valid. Higher budgets require an ADR and performance evidence.

## Runtime outputs

An action receipt records `action_receipt_id`, actor, game, player, input digest, definition digest, engine version, prior and new state versions, logical time, seed metadata, ledger transaction IDs, event IDs, result payload, denial explanation, and request/correlation IDs.

## Extension interface

A new mechanic integrates by registering schemas, pure handlers, state namespace, migrations, actions, effects, events, timers, analytics mappings, and contract tests. It cannot modify the core evaluator dispatch loop. The registry discovers handlers from signed package manifests.
