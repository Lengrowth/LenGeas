# Reusable Terraform modules

Phase 02 modules expose typed variables, outputs, provider constraints, examples,
contract tests, ownership/cost tags, and fail-closed defaults. The environment
roots compose these modules; they do not duplicate provider resources.

Third-party provider modules intentionally expose a disabled contract until the
owner supplies the required account/project identifiers and access. This keeps
plan and evidence generation honest while preserving a reproducible apply path.

