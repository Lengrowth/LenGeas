# Phase 04 handoff

## Status and scope

`in_review`; P04-T01 through P04-T08 have review evidence. The repository owner must explicitly accept this phase. No schema has been published to an external registry.

The independent review corrections are committed on `main` as `1db9a84` (`P04: fix definition schema review findings`). The evidence-only manifest refresh follows separately and binds this source commit.

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

No dashboards or alerts are introduced by the schema-only phase. Validation failures include JSON Pointer, stable code, and severity. No production data is used. Medium risk: internal registry publication awaits a configured registry endpoint and secret-managed credentials; owner: `game_systems_owner`. The checked-in Ed25519 public key verifies the release signature but is not independently trusted, so the current signature does not authenticate a signer. Negative-balance approval metadata is digest-bound but self-asserted; the publishing authority must verify the referenced security review in an authorized system. Runtime loading and full balance simulation begin in Phase 05 and later simulation phases.

## External setup

No credentials are needed for local generation. Registry publication will require a registry endpoint plus a write credential stored in the approved secret manager; no secret value is stored here.

## Exact first command for Phase 05

`uv run --frozen python tools/dev/task_runner.py phase-gate 04`

## Prohibited assumptions

Do not assume Phase 04 is accepted, that an external registry contains schema `0.1.0`, that schema signatures imply owner approval, that the workstation has a production runtime/simulator, or that arbitrary extensions and remote configuration are trusted.
