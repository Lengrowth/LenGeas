# Production environment root

This root composes the complete Phase 02 module set for `production` in
`eu-central-1`. It is disabled by default and uses a separate S3 state key. The
root is safe to initialize and validate without cloud credentials; applying it
requires the inventory, cost estimate, owner decision, and vendor access recorded
in `docs/evidence/phase-02`.

Backend configuration is supplied out of band with a reviewed `-backend-config`
file containing only bucket/key/region/non-secret settings. State is encrypted,
versioned, and locked with native S3 lockfiles.

