# Definition Schema v0.1

The Draft 2020-12 bundle schema is the source of truth. YAML is restricted to a
JSON-compatible subset; canonical bundles use UTF-8 JSON with sorted object
keys, compact separators, normalized decimal strings, and SHA-256 digests.
Schemas reject unknown fields unless they appear inside the registered
`extensions` namespace map.

The package is pinned to schema version `0.1.0`. Published module versions and
digests are exact locks; draft ranges are resolved before publication.
