# Game Definition Schema v0.1

## Authority and packaging

JSON Schema Draft 2020-12 files under `packages/schemas/definition/v0.1/` are the source of truth. YAML is the authoring format and canonical JSON is the validation, hashing, storage, and transport format. A package contains a manifest plus referenced documents. Publication resolves all documents into one canonical bundle.

```text
manifest.yaml
game.yaml
modules/*.yaml
entities/*.yaml
resources/*.yaml
actions/*.yaml
events/*.yaml
timers/*.yaml
progression/*.yaml
quests/*.yaml
achievements/*.yaml
localization/<locale>/*.yaml
extensions/<namespace>/*.yaml
```

## Common header

Every definition object contains:

| Field | Type | Rule |
|---|---|---|
| `id` | stable ID | Unique within object type and game |
| `schema_version` | semantic version | Exactly `0.1.0` for this schema |
| `display_name_key` | localization key | Required for player-visible objects |
| `description_key` | localization key | Required for player-visible objects |
| `tags` | sorted unique string array | Maximum 32 tags |
| `enabled` | boolean | Explicit; no implicit default in published data |
| `metadata` | object | Studio-only labels; forbidden in runtime decisions |
| `extensions` | namespaced object | Each namespace has a registered schema |

## Game

`Game` defines identity and global contract: `id`, `studio_id`, `name`, `genre_labels`, `default_locale`, `supported_locales`, `blueprint`, `network_mode`, `engine_range`, `modules`, `features`, `state_schema_version`, and `definition_schema_version`.

`network_mode` is exactly one of `offline`, `offline_first`, `online_optional`, `online_required`, or `server_authoritative`. The mode fixes which action policies are legal.

## Module

`Module` contains `id`, `version`, `digest`, `engine_range`, `requires`, `conflicts`, `configuration`, `state_namespaces`, `registered_actions`, `subscribed_events`, `emitted_events`, `registered_conditions`, `registered_effects`, `registered_timers`, `migrations`, and `resource_budget`.

Published module resolution stores exact versions and digests. Version ranges exist only in drafts.

## Entity

`Entity` contains `id`, `entity_type`, `initial_state`, `properties`, `tags`, and typed `relationships`. A relationship contains `relationship_type`, `target_type`, `target_id`, and metadata validated by the owning module.

Entities are definition objects. Player-owned instances use `entity_instance_id`, definition reference, instance state, owner, state version, and timestamps.

## Resource

`Resource` contains `id`, `resource_type`, `numeric_model`, `initial_amount`, `minimum`, `maximum`, `overflow_policy`, `visibility`, and `transfer_policy`.

- `numeric_model` is `integer` or `fixed_decimal` with declared scale.
- `overflow_policy` is `reject`, `clamp`, or `route_to_resource`.
- `transfer_policy` is `non_transferable`, `game_internal`, or `cross_game_contract`.
- Negative balances are forbidden unless `minimum` explicitly permits them and the security review approves the resource.

## Condition

Conditions are typed AST nodes:

- composition: `all`, `any`, `not`;
- comparison: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`;
- existence: `exists`;
- temporal: `before`, `after`, `elapsed_at_least` using logical time;
- reference: a registered named predicate with validated arguments.

A value operand is a literal or a bounded state path declared readable by the module. AST depth is at most 32 and node count at most 256.

## Formula

Formulas use a separate numeric AST with `add`, `subtract`, `multiply`, `divide`, `min`, `max`, `clamp`, `floor`, `ceil`, `power_integer`, and `piecewise`. Variables come from an explicit allowlist. Division by zero, overflow, scale loss, excessive depth, and excessive operation count fail validation. Arbitrary strings, loops, reflection, system calls, network access, and dynamic field access do not exist in the language.

## Action

`Action` contains `id`, `input_schema`, `authority`, `idempotency`, `cooldown`, `conditions`, `costs`, `effects`, `rewards`, `emitted_events`, `analytics`, and `rate_limit_class`.

`authority` is `local`, `server`, or `match_server`. Published competitive or value-changing actions cannot be `local`.

## Cost, Effect, and Reward

- `Cost` reserves and consumes value before effects. It names an owner, resource/item/entitlement reference, quantity formula, insufficiency behavior, and ledger reason.
- `Effect` is a typed state operation: `set`, `increment`, `decrement`, `append_unique`, `remove`, `unlock`, `lock`, `grant_item`, `consume_item`, `equip`, `unequip`, `apply_modifier`, `remove_modifier`, `start_timer`, `cancel_timer`, `complete_objective`, or `emit_event`.
- `Reward` is a grant plan with typed entries for resource, item, unlock, entitlement, progression, cosmetic, loot table, or cross-game contract.

Effect paths must belong to the acting module. A reward is granted through the economy/inventory transaction service, never by direct state editing.

## Event

`EventDefinition` contains `type`, `major_version`, `payload_schema`, `producer`, `allowed_consumers`, `retention_class`, `contains_pii`, and `analytics_mapping`. Runtime envelopes follow `09-api-events-jobs-timers.md`.

## Timer

`TimerDefinition` contains `id`, `timer_type`, `authority`, `duration_formula` or `schedule`, `stacking_policy`, `pause_policy`, `on_due_action`, `max_catch_up`, and `offline_policy`.

Types are `one_shot`, `recurring`, `countdown`, `cooldown`, and `scheduled`. Published cron schedules use UTC. Server-authoritative timers never trust a client due time.

## ProgressionNode

`ProgressionNode` contains `id`, `graph_id`, `node_type`, `requirements`, `costs`, `rewards`, `effects`, `dependencies`, `exclusive_group`, `repeat_policy`, and `children`. Publication rejects missing references, cycles in acyclic graphs, unreachable required nodes, and contradictory requirements.

## DefinitionVersion

`DefinitionVersion` contains `id`, `game_id`, `version`, `status`, `schema_version`, `engine_range`, `module_locks`, `bundle_digest`, `parent_version`, `migration_plan`, `release_notes`, `created_by`, approval records, and timestamps.

Statuses are `draft`, `testing`, `staging`, `published`, `deprecated`, and `archived`. Only one version per environment channel is active. Published fields are immutable.

## Validation levels

1. Syntax: YAML parsing, schema validation, sizes, and field types.
2. References: uniqueness, existence, namespace ownership, localization completeness.
3. Graph: cycles, reachability, exclusive paths, dependency order.
4. Semantic: legal authority, costs, rewards, formulas, timers, and network-mode constraints.
5. Safety: operation budgets, remote-config allowlist, PII, entitlements, and cross-game boundaries.
6. Runtime: load bundle and execute conformance actions.
7. Simulation: mandatory balance and invariant suites.

A definition cannot advance to staging until all seven levels pass.

## Schema evolution

Patch versions add clarifications and constraints without changing valid serialized meaning. Minor versions add optional constructs plus migration tooling. Major versions change meaning or remove constructs. Publication stores the exact schema digest used for validation.
