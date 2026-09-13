# Phase 01 Blockers

## BLK-01 — Docker runtime unavailable locally — resolved by authorized server run

The repository owner directed that Docker must not be installed or run locally. That workstation restriction remains in force. The authorized AWS host `i-0e826e65d7f5df890` runs Docker Engine `29.8.0` and Compose `5.5.1`; the complete server-side smoke passed and is recorded in `operations/server-runtime.json`.

Owner: `platform_operations_owner`; status: resolved for Phase 01 runtime evidence; resolution: retain the server-only execution boundary.

## BLK-02 — E2E endpoint unavailable — resolved by server-local endpoint

The server-side E2E harness passed with `LENGEAS_E2E_BASE_URL=http://127.0.0.1:8000`, and the public E2E harness now passes with `LENGEAS_E2E_BASE_URL=https://games.lengrowth.com`; both results are recorded in `operations/server-runtime.json`.

Owner: `qa_owner`; status: resolved; resolution: retain both server-local and public E2E checks.

## BLK-03 — Remote repository protection and CI gate unavailable

The remote is configured and pushed; `origin/main` is `d012034b829d1c8f2ee81f74a35c6c5c7bbc9b5b`. GitHub metadata now confirms public repository `guerra2fernando/LenGeas`, default branch `main`, owner admin permission, and Actions enabled with all actions allowed. The live branch read reports `protected: false` and required status-check enforcement `off`. The full verification dispatch run `34758013015` was accepted but the job was not started because the account is locked due to a billing issue. No successful CI run or live protection export can be claimed until billing is restored and `main` is protected. P01-T08 still contains the local policy intent and the observed live state.

Owner: `infrastructure_owner`; status: open; resolution: clear the GitHub billing lock, enable the required `main` protection, and attach a successful CI run without weakening the local policy.

## BLK-05 — Public DNS/TLS cutover — resolved

`games.lengrowth.com` resolves to `3.238.63.61`. Caddy obtained a valid production certificate, `https://games.lengrowth.com/health` and `/version` return the expected API responses, and public E2E passes. The record is currently DNS-only; Cloudflare proxying can be enabled after this direct-origin validation if desired.

Owner: `infrastructure_owner`; status: resolved; resolution: retain the DNS record and certificate, or optionally enable Cloudflare proxying with Full (strict).

## BLK-04 — Sigstore sample verification unavailable

The release metadata and workflow require keyless Sigstore signing, but `cosign` and a CI OIDC identity are unavailable locally. The repository owner explicitly said signing is not needed for this temporary server deployment; that authorization is recorded, but it does not silently waive the Phase 01 mandatory signing gate. No signature is claimed.

Owner: `release_manager`; status: open; resolution: run the release workflow or an equivalent ephemeral OIDC environment and attach verification output.
