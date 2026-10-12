# Phase 05 open risks and evidence gaps

The repository owner explicitly accepted Phase 05 on 2026-10-12 with the
following evidence gaps disclosed. Acceptance records the owner's decision; it
does not claim that any unavailable integration, hosted run, or signature was
completed.

No Phase 04 entry blocker existed when implementation began: its manifest was
`accepted`, and the exact entry gate and evidence verification passed.

Open evidence gaps accepted with Phase 05:

- Docker is not installed on this workstation. The full
  `task test:integration` command failed closed before executing the local
  Compose/MongoDB suite. Mongo transaction crash injection, transient-error
  handling, version races, and transaction-result uncertainty were not
  exercised against MongoDB.
- `task test:e2e` failed closed because `LENGEAS_E2E_BASE_URL`,
  `LENGEAS_E2E_GUEST_PROOF`, and `LENGEAS_E2E_DEVICE_PUBLIC_KEY` are unset.
  Local API TestClient E2E tests passed.
- The ARM64 and x86-64 GitHub Actions matrix is configured but has not run from
  this checkout. The local AMD64 replay passed; no ARM64 result is claimed.
- No owner-managed signing key is configured. The local replay report is
  explicitly unsigned.
- Production runtime API composition still needs the Phase 03 trusted principal
  provider and durable Mongo repository; local E2E uses the in-memory adapter.
- The benchmark's reference CPU threshold still needs confirmation on the
  designated runner.

These conditions remain represented as open risks in `manifest.json`. The
acceptance does not claim completion of these external checks.
