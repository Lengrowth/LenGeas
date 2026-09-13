# Phase 13 — Solo Mechanics Packages

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Implement mechanics through package interfaces; editing core dispatch to accommodate a package fails the phase.

## Mission

Release idle, prestige, story, RPG, cards, merge, tower defense, crafting, and management packages with schemas, runtime, Studio, simulation, analytics, migrations, and conformance.

## Required reading and entry

Phase 12 must be accepted. Read its handoff and `05-game-definition-schema-v0.1.md`, `06-runtime-and-rules.md`, `11-saves-offline-sync.md`, `12-simulation-balance-experiments-analytics.md`, `14-mechanics-packages.md`, and package/module ADRs.

## Standard package output

Every `mechanics/<id>/` contains `manifest.yaml`, `schemas/`, pure `runtime/`, `migrations/`, `simulation/`, `studio/`, `analytics/`, `tests/{unit,property,contract,determinism,performance,security}/`, `CHANGELOG.md`, and `README.md`. The internal registry receives a signed immutable artifact and SBOM. Package state is namespaced by package ID.

## Tasks and exact acceptance

- [ ] **P13-T01 — Idle and prestige.** Implement generators, resource chains, automation, multipliers, exponential/linear/piecewise costs, aggregated offline progress, unlocks, prestige eligibility, reset/retain plan preview, reward, history, and repeat scaling. Prove tick/aggregate equivalence over 30 days and repeated prestige idempotency.
- [ ] **P13-T02 — Story.** Implement scenes, speakers, dialogue, choices, variables, conditions/effects, branch/exclusive/merge rules, checkpoints, history, localization, graph editor, and traversal strategies. Reject missing destinations and required unreachable scenes.
- [ ] **P13-T03 — RPG.** Implement attributes, levels, experience, slots, equipment hooks, typed modifiers, abilities, cooldowns, statuses, turn combat, deterministic targeting, loot, defeat/recovery, editors, and strategies. Prove combat replay and modifier order.
- [ ] **P13-T04 — Cards.** Implement card/deck/hand/draw/discard/exile/board zones, deck legality, seeded shuffle, draws, turns, legal moves, effects, win/draw, replay, editor, and strategies. Prove no hidden-state leak and exact shuffle replay.
- [ ] **P13-T05 — Merge.** Implement board topology, typed cells, occupancy, spawn tables, move validation, recipes, cascades, energy hooks, progression, undo policy, editor, and strategies. Prove atomic board mutation and no overwrite/duplication.
- [ ] **P13-T06 — Tower defense.** Implement map/path validation, waves, spawns, towers, targeting, projectiles, enemies, fixed-step movement, damage, armor, status, heroes, win/loss, editor, and strategies. Prove identical fixed-step results without renderer timing.
- [ ] **P13-T07 — Crafting and management.** Implement recipe/station/input reservation/queue/timer/cancel/claim plus facility/worker/assignment/demand/capacity/maintenance/production/scenario objectives. Prove atomic reservation, idempotent claims, catch-up, and capacity limits.
- [ ] **P13-T08 — Combination certification.** Create explicit pairwise manifests and combined synthetic blueprints; test dependency order, namespace access, event loops, modifier conflicts, timer volume, save migration order, Studio forms, simulation hooks, and performance budgets.
- [ ] **P13-T09 — Registry lifecycle.** Install, configure, publish with, upgrade, migrate, roll back, deprecate, revoke, and audit every package through Studio and public APIs.

## Cross-package fixtures

Fixtures must combine idle+prestige, story+RPG, RPG+cards, merge+crafting, management+idle, and tower-defense+RPG. They remain tiny rule probes named `fixture_*`; no art, narrative campaign, balance content, or game client is allowed.

## Mandatory tests and evidence

For every package run schema invalid/valid fixtures, unit/property tests, 1,000-seed replay on ARM64/x86, all supported save migrations, simulator profile, Studio create/edit/diff, event catalog validation, analytics partition validation, security resource-budget abuse, and reference CPU performance. Store per-package signed release report, digest, SBOM, compatibility row, and benchmark under `docs/evidence/phase-13/packages/<id>/`.

## Gate and handoff

`task phase:gate PHASE=13` fails if core runtime changed except through an accepted generic extension ADR. Handoff to Phase 14 provides package digests, state/action/event catalogs, match-compatible hooks for cards and tower defense, SDK types, compatibility matrix, and performance budgets.
