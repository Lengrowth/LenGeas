# Phase 01 Blockers

## BLK-01 — Docker runtime unavailable locally — resolved by authorized server run

The repository owner directed that Docker must not be installed or run locally. That workstation restriction remains in force. The authorized AWS host `i-0e826e65d7f5df890` runs Docker Engine `29.8.0` and Compose `5.5.1`; the complete server-side smoke passed and is recorded in `operations/server-runtime.json`.

Owner: `platform_operations_owner`; status: resolved for Phase 01 runtime evidence; resolution: retain the server-only execution boundary.

## BLK-02 — E2E endpoint unavailable — resolved by server-local endpoint

The server-side E2E harness passed with `LENGEAS_E2E_BASE_URL=http://127.0.0.1:8000`; the synthetic health flow is recorded in `operations/server-runtime.json`. Public hostname validation remains separately tracked as BLK-05.

Owner: `qa_owner`; status: resolved for server-local E2E evidence; resolution: validate the public hostname after DNS/TLS cutover.

## BLK-03 — Remote repository protection and CI gate unavailable

The remote is configured and pushed; `origin/main` is `d9f6715f3f997487c5cb0075b518ecb60c1aaa9e`. GitHub metadata confirms private repository `guerra2fernando/LenGeas`, default branch `main`, owner admin permission, and Actions enabled with all actions allowed. The live branch read reports `protected: false` and required status-check enforcement `off`. After correcting the invalid action refs and adding `workflow_dispatch`, every registered verification push still ends in zero-job `startup_failure`; the latest is run `34756975179` for the audited commit. A temporary valid one-step `ci-probe` also ended in zero-job `startup_failure`, proving the failure is external to LenGeas workflow steps and local Docker. The authenticated integration returned `403 Resource not accessible by integration` for branch protection and `403 Upgrade to GitHub Pro or make this repository public` for rulesets, so no live protection configuration can be changed or exported through this connection. P01-T08 still contains the local policy intent and the observed live state.

Owner: `infrastructure_owner`; status: open; resolution: use the repository owner's GitHub plan/settings access to make hosted Actions runnable, enable the required `main` protection, and attach a successful CI run without weakening the local policy.

## BLK-05 — Public DNS/TLS cutover unavailable

The server and Caddy reverse proxy are healthy at `3.238.63.61`, but the Wrangler OAuth token has only `zone:read` and cannot read or update DNS records. `games.lengrowth.com` still resolves through the prior Cloudflare edge record, so public HTTPS validation is intentionally not claimed.

Owner: `infrastructure_owner`; status: open; resolution: grant the Cloudflare token DNS Read/Write or update the exact `A` record `games.lengrowth.com` to `3.238.63.61`; then verify HTTPS and rerun public E2E.

## BLK-04 — Sigstore sample verification unavailable

The release metadata and workflow require keyless Sigstore signing, but `cosign` and a CI OIDC identity are unavailable locally. The repository owner explicitly said signing is not needed for this temporary server deployment; that authorization is recorded, but it does not silently waive the Phase 01 mandatory signing gate. No signature is claimed.

Owner: `release_manager`; status: open; resolution: run the release workflow or an equivalent ephemeral OIDC environment and attach verification output.
