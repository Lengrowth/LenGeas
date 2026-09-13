# Phase 01 — Engineering Foundation

## Goal

Create the reproducible monorepo, local development environment, contract toolchain, and protected delivery workflow.

## Entry

Phase 00 is accepted.

## Tasks

- [ ] **P01-T01 — Scaffold monorepo.** Create the exact directory structure in `04-repository-and-engineering-standard.md`, pnpm/Turborepo workspace, uv workspace, root task commands, and ownership files. Evidence: clean bootstrap log.
- [ ] **P01-T02 — Pin toolchains.** Pin Python, Node, pnpm, uv, Terraform, Docker base images, linters, type checkers, and test tools. Depends on P01-T01. Evidence: lockfiles and version report.
- [ ] **P01-T03 — Build local platform.** Docker Compose starts MongoDB replica set, Valkey, RabbitMQ, Kafka-compatible Redpanda test broker, local R2-compatible storage, mail sink, API health/version shell, and telemetry collector. Depends on P01-T01. Evidence: one-command smoke report.
- [ ] **P01-T04 — Establish CI.** GitHub Actions runs formatting, lint, strict types, unit tests, schemas, Terraform validation, secret scan, dependency scan, container scan, SBOM, docs links, and license policy. Depends on P01-T02. Evidence: protected-branch checks.
- [ ] **P01-T05 — Establish artifact provenance.** Configure immutable build metadata, Sigstore signing, SBOM storage, and release manifest generation. Depends on P01-T04. Evidence: verified sample artifact.
- [ ] **P01-T06 — Create contract generators.** Establish JSON Schema validation, canonical JSON, schema-to-Python/TypeScript generation, and OpenAPI diff checks. Depends on P01-T02. Evidence: deterministic generated-output test.
- [ ] **P01-T07 — Create test harnesses.** Add unit, property, contract, integration, E2E, load, security, and determinism test projects with fixture naming rules. Depends on P01-T01. Evidence: empty-suite contract checks.
- [ ] **P01-T08 — Protect repository.** Configure branch policy, CODEOWNERS, PR template, task evidence links, dependency automation, and signed release tags. Evidence: policy screenshot/export.

## Exit gate

A fresh machine clones the repository, runs one bootstrap command, starts the local dependencies, executes all checks, and reproduces signed sample artifacts. No manual setup beyond documented credentials is required.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read the Phase 00 handoff, ADRs 0003/0006/0008/0010, `03-technology-standard.md`, `04-repository-and-engineering-standard.md`, and `19-testing-and-quality-gates.md`. Do not implement domain behavior.

### Exact outputs

- Root: `.tool-versions`, `.editorconfig`, `.gitattributes`, `.gitignore`, `Taskfile.yml`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `turbo.json`, `pyproject.toml`, `uv.lock`, and `CODEOWNERS`.
- Local stack: `compose.yaml`, `infrastructure/docker/**`, `tools/dev/**`, and a secret-free `.env.example`.
- CI: `.github/workflows/{verify,release,dependency-review,codeql}.yml`, Dependabot configuration, PR template, and generated evidence upload.
- Contracts: `packages/schemas/evidence/phase-manifest.schema.json`, canonical JSON vectors, generator configuration, test marker policy.
- Typed empty shells for every app/package/mechanic path in the repository standard. Shells expose health/version only.

`task local:up` starts MongoDB replica set, Valkey, RabbitMQ, Redpanda, MinIO, Mailpit, OpenTelemetry Collector, Prometheus, Grafana, and Jaeger. `task local:smoke` proves Mongo transactions, broker publish/consume, S3 put/get, and trace export. Reject `latest`, caret/tilde dependency ranges, unpinned image digests, silent mandatory-test skips, or generators that create a diff on their second run.

### Required verification

On clean Windows and Ubuntu clones run `task bootstrap`, `task local:up`, `task local:smoke`, `task generate` twice, `task verify`, `task evidence PHASE=01`, and `task local:down`. Record tool versions, commands, exit codes, durations, artifact digests, SBOM, signature verification, and repository-policy export.

### Handoff to Phase 02

Provide locked-tool report, CI workflow digests, local service map, Terraform provider policy, GitHub OIDC claims, generated evidence-schema digest, and exact infrastructure validation commands.
