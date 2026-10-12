# Phase 05 blockers and external evidence gaps

No Phase 04 entry blocker existed when implementation began: its manifest was `accepted`, and the exact entry gate and evidence verification passed.

Phase 05 remains `in_review`. These external results are still required before its evidence is complete for acceptance:

- Docker is not installed on this workstation. The full `task test:integration` command failed closed before executing the local Compose/MongoDB suite. Mongo transaction crash injection, transient-error handling, version races, and transaction-result uncertainty were not exercised against MongoDB.
- `task test:e2e` failed closed because `LENGEAS_E2E_BASE_URL`, `LENGEAS_E2E_GUEST_PROOF`, and `LENGEAS_E2E_DEVICE_PUBLIC_KEY` are unset. Local API TestClient E2E tests passed.
- The ARM64 and x86-64 GitHub Actions matrix is configured but has not run from this checkout. The local AMD64 replay passed; no ARM64 result is claimed.
- No owner-managed signing key is configured. The local replay report is explicitly unsigned.

These conditions are represented as open risks in `manifest.json`; they do not alter Phase 04 or record repository-owner acceptance for Phase 05.
