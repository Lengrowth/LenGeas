# Phase 04 implementation decisions

- The accepted Draft 2020-12 contract in `docs/05-game-definition-schema-v0.1.md` and `docs/14-mechanics-packages.md` remains authoritative. No architecture choice or dependency was changed.
- `packages/schemas/definition/v0.1/bundle.schema.json` is the source schema catalog; per-definition schema files and Python/TypeScript models are generated from it.
- Authoring YAML is restricted to a deterministic safe subset. Canonical JSON is compact UTF-8 with recursively sorted object keys; package arrays are sorted by stable ID before hashing.
- Runtime and simulation validation levels use deterministic schema/validator conformance checks. They do not claim a production game runtime or balance simulator exists in Phase 04.
- Internal registry publication cannot run without a configured endpoint and secret-managed credentials. A locally verifiable signed release is included for owner review.
