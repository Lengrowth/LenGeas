# TypeScript SDK shell

Generated contract-facing SDK boundary.

# TypeScript SDK

`src/definition-v0_1.ts` contains generated v0.1 definition shapes and schema validators backed by the canonical Draft 2020-12 bundle schema. Use `validateDefinitionSchema(name, value)` for a named generated definition or `validateDefinitionBundle(value)` for the complete bundle. Regenerate with `task generate`.

Validators return `{ valid, value, errors }` for valid definitions and `{ valid, errors }` for invalid definitions. Schema failures use JSON Pointers and the stable `schema_validation` code. They validate structural schema only. Use the Python CLI for YAML parsing, package-size limits, references, graph checks, semantic constraints, and safety policy.
