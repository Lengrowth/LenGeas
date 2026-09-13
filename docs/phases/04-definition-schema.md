# Phase 04 — Definition Schema v0.1

## Goal

Publish canonical, generated, fully validated contracts for every universal primitive and module manifest.

## Entry

Phase 03 is accepted; P01-T06 contract generation is available.

## Tasks

- [ ] **P04-T01 — Define common schemas.** Implement IDs, headers, localization keys, tags, metadata, extensions, numeric values, timestamps, references, and canonicalization. Evidence: golden schema fixtures.
- [ ] **P04-T02 — Define blueprint and module schemas.** Implement Game, network mode, features, module manifest, dependencies, namespaces, budgets, and exact release locks. Depends on P04-T01. Evidence: dependency validation suite.
- [ ] **P04-T03 — Define primitive schemas.** Implement Entity, StatePath, Resource, Condition, Formula, Action, Cost, Effect, Reward, Event, Timer, Relationship, and ProgressionNode. Depends on P04-T01. Evidence: positive/negative fixture suite.
- [ ] **P04-T04 — Define domain schemas.** Implement item, inventory, quest, achievement, entitlement, localization, LiveOps, experiment, analytics, save, match, and cross-game contract schemas. Depends on P04-T03. Evidence: reference suite.
- [ ] **P04-T05 — Implement validation pipeline.** Deliver seven validation levels, structured errors, reference resolution, graph analysis, formula budgets, module compatibility, and safety rules. Depends on P04-T02–T04. Evidence: validation conformance report.
- [ ] **P04-T06 — Implement canonical bundle.** Resolve YAML package into canonical JSON, sort deterministically, calculate SHA-256, sign manifest, and read-back verify. Depends on P04-T05. Evidence: reproducibility across OS/architecture.
- [ ] **P04-T07 — Generate model libraries.** Generate Python and TypeScript types/validators plus documentation from the same schemas. Depends on P04-T03–T06. Evidence: zero-diff regeneration.
- [ ] **P04-T08 — Freeze schema v0.1.** Run architecture/security/game-systems review, assign compatibility policy, publish schema artifact to internal registry. Depends on P04-T01–T07. Evidence: signed schema release.

## Exit gate

Schema `0.1.0` is signed, immutable, generated models match, invalid fixtures fail with stable codes, and canonical bundles reproduce byte-for-byte on supported environments.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 03 handoff, ADRs 0006/0007, principles, repository standard, schema contract, and mechanics schema sections.

### Exact outputs

`packages/schemas/definition/v0.1/` contains `bundle.schema.json`; common ID/header/reference/localization/numeric/state-path schemas; core game/module/entity/resource/condition/formula/action/cost/effect/reward/event/timer/progression schemas; domain item/inventory/quest/achievement/entitlement/LiveOps/experiment/analytics/save/match/cross-game schemas; and extension manifest. Add generated Python/TypeScript packages, schema tools, reference docs, and `tests/conformance/fixtures/definitions/{valid,invalid}/`.

Each invalid fixture contains `input.yaml` and `expected-errors.json` with JSON Pointer, stable code, and severity. Each valid fixture contains canonical JSON and SHA-256. Include boundary fixtures at and above every AST/bundle/string/array/numeric limit.

### Parser and validation constraints

Reject YAML anchors, aliases, custom tags, duplicate keys, NaN, infinity, implicit timestamps, and non-string object keys. Reject unknown fields outside a registered extension namespace. Resolve references as IDs. Validate duplicates, missing targets, package cycles/conflicts, namespace violations, progression cycles/unreachability, impossible ranges, reward loops, remote-config illegality, localization gaps, overflow, division by zero, operation budgets, canonical order, and decimal normalization.

Run `task generate` twice with zero second-run diff, validation on all fixtures, schema compatibility, cross-OS digest, generated-model compilation, documentation generation, and `task phase:gate PHASE=04`.

### Handoff to Phase 05

Provide schema-registry interface, generated-model imports, validator/canonicalizer CLIs, schema/bundle digests, minimal valid fixture, invalid-fixture catalog, and frozen AST operator registry.
