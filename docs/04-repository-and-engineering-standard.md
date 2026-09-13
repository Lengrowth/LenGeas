# Repository and Engineering Standard

## Target monorepo

```text
LenGeas/
  apps/
    studio/                 # Next.js Game Studio
    api/                    # FastAPI composition root
    realtime-gateway/       # WebSocket ingress
    match-service/          # authoritative sessions
    workers/                # Celery and event consumers
  packages/
    schemas/                # canonical JSON Schema files
    runtime/                # pure Python rule runtime
    domain/                 # domain models and policies
    persistence/            # MongoDB, Valkey, outbox adapters
    simulation/             # headless simulation
    sdk-python/
    sdk-typescript/
    sdk-csharp/
    sdk-kotlin/
    sdk-swift/
    shared-types/           # generated types and fixtures
  mechanics/
    idle/
    prestige/
    story/
    rpg/
    cards/
    merge/
    tower-defense/
    crafting/
    management/
    async-multiplayer/
    realtime-session/
  infrastructure/
    terraform/
      bootstrap/
      modules/
      environments/
    docker/
    policies/
  docs/
  tests/
    contract/
    conformance/
    integration/
    performance/
    security/
    disaster-recovery/
  tools/
```

No game directory exists before platform completion. Conformance definitions live under `tests/conformance/fixtures` and use names beginning with `fixture_`.

## Branch and review model

- `main` is protected and always releasable.
- Work uses short-lived branches named `<type>/<task-id>-<slug>`.
- Every commit references a phase task ID.
- Pull requests require green checks, one domain owner review, and CODEOWNER review for schemas, infrastructure, security, or migrations.
- Production deployment requires an immutable Git tag, signed image digests, and environment approval.
- Direct pushes, force pushes, and merge commits to `main` are disabled. Squash merge is the only merge method.

## Task contract

Every task record states owner role, requirements, dependencies, artifacts, tests, rollout, rollback, observability, security impact, and acceptance evidence. A checkbox without linked evidence is incomplete.

## Naming and identifiers

- Internal object IDs use UUIDv7 lowercase strings.
- Human-authored stable definition IDs use lowercase ASCII snake case and match `^[a-z][a-z0-9_]{2,63}$`.
- API JSON fields use `snake_case`; TypeScript adapters expose generated camel-case accessors without changing wire names.
- Event types use `<domain>.<fact>.v<major>`, such as `economy.resource_spent.v1`.
- R2 object keys use `<environment>/<studio_id>/<game_id>/<artifact_type>/<digest>`.
- MongoDB collections use plural snake case.

## Time, numbers, and serialization

- Persistent timestamps use UTC RFC 3339 with microseconds and `Z`.
- Durations use integer milliseconds on APIs and integer microseconds inside the runtime.
- Currency and countable resources use signed 64-bit integers in the smallest declared unit.
- Fixed fractional values use normalized decimal strings on APIs and Decimal128 in MongoDB.
- Authoritative random selection uses PCG64 with a supplied 128-bit seed; the algorithm version is stored with the result.
- Canonical JSON and SHA-256 follow the determinism rules in `01-principles-and-invariants.md`.

## Error model

Every API error includes:

```json
{
  "error": {
    "code": "condition_failed",
    "message": "The action requirements are not satisfied.",
    "request_id": "uuidv7",
    "details": [],
    "retryable": false
  }
}
```

Codes are stable. Messages are not parsed by clients. Stack traces are never returned.

## Compatibility

- Additive optional API response fields are backward-compatible.
- Removing or retyping a field requires a new API major version.
- Event consumers support the current and previous event major during migration.
- Save migrations support every production save schema that remains inside the retention window.
- Published definitions pin an engine compatibility range and every package digest.

## Documentation maintenance

The task changing behavior updates the contract document, OpenAPI/schema artifact, ADR when required, phase evidence, runbook, and traceability row in the same pull request.
