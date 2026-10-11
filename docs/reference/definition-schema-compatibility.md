# Definition schema compatibility policy

Definition schema `0.1.0` is the pinned contract used to validate and hash each published bundle. The exact schema digest is recorded in every release manifest.

- **Patch** changes clarify or tighten validation without changing the meaning of valid serialized data. A patch must include compatibility fixtures proving previously valid canonical bundles remain valid.
- **Minor** versions add optional fields, enum values, or registered extension points and include a deterministic migration path. Existing valid bundles retain their meaning.
- **Major** versions may remove fields or change serialized meaning. They require an explicit migration and a new major schema identifier.

Published bundles pin an exact schema version and digest. Draft module dependency ranges are resolved before publication; release locks store exact semantic versions and SHA-256 digests. Unknown fields are rejected unless they appear in an extension namespace registered by the bundle's extension manifest. A release is immutable after signing.
