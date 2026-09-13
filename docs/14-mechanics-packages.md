# Mechanics Package Contracts

## Package standard

Every mechanics package ships a manifest, configuration schema, state schemas, pure runtime handlers, events, analytics mappings, save migrations, simulation strategy hooks, Studio editor metadata, documentation, and conformance tests. Packages communicate through core actions and events. They never write another package's state namespace.

## Required v1 packages

### Idle

Owns generators, production chains, automation, offline aggregation, multipliers, purchase scaling, and generator unlocks. Production uses logical time and fixed-precision formulas. Offline aggregation and tick-by-tick execution must produce equivalent canonical results within declared rounding rules.

### Prestige

Owns prestige eligibility, reset scopes, retained scopes, prestige rewards, history, and repeat scaling. Prestige executes as one idempotent action. Reset plans are previewable and cannot target undeclared namespaces.

### Story

Owns scenes, dialogue, choices, variables, branches, checkpoints, and story history. Choice conditions and effects use core primitives. Published graphs reject missing destinations and required unreachable scenes.

### RPG

Owns attributes, levels, experience curves, equipment slots, modifiers, abilities, status effects, deterministic combat turns, loot tables, and progression hooks. Inventory ownership and resource value remain core services.

### Cards

Owns card definitions, decks, zones, draw/shuffle, turn order, legal move evaluation, effects, and deterministic match replay. Shuffles use the runtime seed and record the RNG algorithm version.

### Merge

Owns board topology, cell occupancy, spawn tables, merge recipes, move validation, energy hooks, and board progression. Board mutations use one action plan and cannot overwrite occupied cells without an explicit rule.

### Tower defense

Owns maps, paths, waves, towers, targeting policies, enemies, damage resolution, status effects, heroes, and deterministic fixed-step combat. Authoritative sessions calculate combat on the match service. Rendering interpolation is client-only.

### Crafting

Owns recipes, stations, inputs, outputs, queues, durations, cancellation, and claim actions. Costs reserve atomically, timers are core timers, and claims are idempotent.

### Management

Owns facilities, workers, assignments, demand, production scheduling, capacity, maintenance, and scenario objectives. Economy transfer remains in core transactions.

### Async multiplayer

Owns turn submission, deadlines, snapshots, challenge flow, replay validation, forfeits, and deterministic resolution. It uses core match, social, rating, and reward services.

### Realtime session

Owns session input schema, tick policy, input buffer, reconnection, deterministic match state, snapshots, and replay. It uses the authoritative match service and does not own matchmaking or persistent rewards.

## Cross-package rules

- A blueprint explicitly installs packages and exact versions.
- Package dependency graphs are acyclic.
- Shared concepts remain core: identity, resources, inventory, actions, conditions, effects, rewards, events, timers, ledgers, saves, experiments, and analytics.
- A package cannot require another package through an undocumented state-path dependency.
- Package combinations require pairwise contract suites and a full blueprint conformance suite.
- Packages expose UI-agnostic state and commands. No renderer, animation, audio, or input-device code belongs in a package.

## Conformance scenarios

Each package has small synthetic definitions that test one rule at a time, boundary values, deterministic replay, migrations, invalid schemas, performance budgets, and combinations with required dependencies. These fixtures are not games and contain no release content.

## Package release gate

A release passes only when schemas, unit tests, property tests, deterministic replay across 1,000 seeds, save migration fixtures, cross-package contracts, simulator hooks, Studio authoring, security review, performance budgets, and documentation all pass.
