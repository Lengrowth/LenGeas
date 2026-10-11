# Phase 04 implementation decisions

- The accepted Draft 2020-12 contract in `docs/05-game-definition-schema-v0.1.md` and `docs/14-mechanics-packages.md` remains authoritative. No architecture choice or dependency was changed.
- `packages/schemas/definition/v0.1/bundle.schema.json` is the source schema catalog; per-definition schema files and Python/TypeScript models are generated from it.
- Authoring YAML is restricted to a deterministic safe subset. Canonical JSON is compact UTF-8 with recursively sorted object keys; package arrays are sorted by stable ID before hashing.
- Module dependency ranges use the v0.1 subset `*`, exact `M.m.p`, `^M.m.p`, and `~M.m.p`; installed module versions must satisfy the range. Unsupported range syntax is rejected.
- Extension schemas are checked as Draft 2020-12 schemas and may use resolvable local JSON Pointer references only. Validation does not retrieve remote schemas.
- Runtime and simulation levels report `conformance_only`; definition validation reports `staging_eligible: false` because Phase 04 has no runtime executor or balance simulator.
- Internal registry publication cannot run without a configured endpoint and secret-managed credentials. A locally verifiable signed release is included for owner review.
- The release verifier checks the signature and current digest manifest, but its checked-in public key has no independent trust anchor. The signature establishes integrity relative to that key, not signer identity; an owner-managed trusted key is still required before registry publication.
