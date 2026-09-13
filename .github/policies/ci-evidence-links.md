# CI and evidence-link policy

Every pull request must make its validation evidence discoverable from the PR description and task record. A checkbox without a linked, reproducible result is incomplete.

## Required links

- The task record under `docs/evidence/phase-01/tasks/`.
- The command log under `docs/evidence/phase-01/commands.ndjson`.
- The phase manifest and blocker record when the change affects phase status.
- Security, performance, operations, SBOM, provenance, or signature artifacts when applicable.

Links must be repository-relative paths or stable CI artifact URLs. Link the exact artifact, not a dashboard summary. External results that cannot run must be recorded as unavailable blockers with the attempted command and exit code.

## Required CI behavior

The protected `main` policy requires strict, successful status checks from the documented `verify`, dependency-review, and CodeQL workflows. Checks must fail closed: missing evidence, invalid links, stale generated output, failed mandatory suites, unsigned release artifacts, and unverifiable provenance block merge.

The one-developer model means the repository owner may perform the required review directly. It does not create a second reviewer, team, account, or GitHub handle.

## Local verification boundary

This checkout has no configured Git remote. Therefore live GitHub checks, branch protection, workflow runs, status contexts, artifact URLs, and screenshots are unavailable. The local policy intent and link requirements are verifiable from this repository; they are not evidence that GitHub has enforced them.
