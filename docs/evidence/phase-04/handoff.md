# Phase 04 handoff

## Status and scope

`accepted`; the repository owner explicitly accepted Phase 04 on 2026-10-12 after reviewing its implementation and evidence. P04-T01 through P04-T08 are accepted. The full GitHub verify workflow and Ubuntu/Windows digest matrix passed on accepted commit `efb7ddc7c07eff27fc18d3663c29743c4b1f9405` ([run 38227181466, attempt 2](https://github.com/Lengrowth/LenGeas/actions/runs/38227181466/attempts/2)). Attempt 1 hit a transient local API health startup failure and was rerun successfully. No schema has been published to an external registry; no registry endpoint or secret-managed credential is configured.

The independent review corrections are on `main`, including `1db9a84` (`P04: fix definition schema review findings`), `d383496` (`P04-T07: generate TypeScript definition validators`), and `595aeee` (scope validator toolchain metadata to Phase 04). The accepted manifest's `final_commit` identifies the verified Phase 04 source candidate; this acceptance update records the owner's decision and the final evidence hashes.

## Operational interfaces

- Schema source: `packages/schemas/definition/v0.1/bundle.schema.json`, Draft 2020-12, version `0.1.0`.
- Generated schemas: `packages/schemas/definition/v0.1/{common,core,domain}/` and `extension-manifest.schema.json`.
- Python models: `packages/sdk-python/definition_v0_1.py`; TypeScript models: `packages/sdk-typescript/src/definition-v0_1.ts`.
- The generated TypeScript model module exports `validateDefinitionSchema(name, value)` for named generated definitions and `validateDefinitionBundle(value)` for the complete bundle. These Ajv Draft 2020-12 structural validators return JSON Pointer errors with stable `schema_validation` codes. They do not replace the Python CLI's YAML parsing, package-size, reference, graph, semantic, and safety checks.
- Validator: `uv run --frozen python tools/dev/definition_cli.py validate <bundle.yaml>`.
- Package canonicalizer: `uv run --frozen python tools/dev/definition_cli.py canonicalize-package <package-dir>`.
- Schema compatibility/determinism: `task definition:compatibility` and `task definition:determinism`.
- The canonical bundle fixture is `tests/conformance/fixtures/definitions/valid/minimal-bundle/`; its SHA-256 is recorded in its `sha256.txt`.
- Signed schema release and detached signature are under `docs/evidence/phase-04/operations/`.
- Validator `valid` means schema/reference/graph/semantic/safety checks pass. `staging_eligible` is always false in Phase 04; runtime and simulation levels report `conformance_only` until their consumers exist.
- Module dependency ranges are restricted to `*`, exact `M.m.p`, `^M.m.p`, and `~M.m.p`; installed versions are checked against each range. Extension schemas must be valid Draft 2020-12 schemas and may reference local definitions only.
- Frozen normalized catalog digest: `6398ea5ac5b6880b567d127b8e3e03f2f85200034376673da079052031b3b1a8`; canonical minimal bundle digest: `c2dce5b74509d7afa505876247d8cbb400c965c51ef9f00b374cfca91872c953`.

## Rollout and rollback

No database migration, runtime rollout, or feature flag was applied. Schema/model changes are versioned source artifacts. Rollback is a reviewed revert before Phase 05 consumes schema `0.1.0`; after adoption, use the documented schema migration policy rather than editing published bytes.

## Operations and risk

No dashboards or alerts are introduced by the schema-only phase. Validation failures include JSON Pointer, stable code, and severity. No production data is used. Accepted follow-up risks: internal registry publication awaits a configured registry endpoint and secret-managed credentials; the checked-in Ed25519 public key has no independent trust anchor; negative-balance approval metadata is self-asserted and must be independently verified by a publishing authority; runtime loading and full balance simulation remain outside Phase 04 and are reported as `conformance_only`. Phase 05 consumes the frozen checked-in schema digest; it must not assume an external registry already contains schema `0.1.0`.

## External setup

No credentials are needed for local generation. Registry publication will require a registry endpoint plus a write credential stored in the approved secret manager; no secret value is stored here.

## Exact first command for Phase 05

`uv run --frozen python tools/dev/task_runner.py phase-gate 04`

## Prohibited assumptions

Do not assume Phase 04 is accepted, that an external registry contains schema `0.1.0`, that schema signatures imply owner approval, that the workstation has a production runtime/simulator, or that arbitrary extensions and remote configuration are trusted.
