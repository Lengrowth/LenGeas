# Phase 01 Blockers

## BLK-01 — Docker runtime unavailable locally — resolved by authorized server run

The repository owner directed that Docker must not be installed or run locally. That workstation restriction remains in force. The authorized AWS host `i-0e826e65d7f5df890` runs Docker Engine `29.8.0` and Compose `5.5.1`; the complete server-side smoke passed and is recorded in `operations/server-runtime.json`.

Owner: `platform_operations_owner`; status: resolved for Phase 01 runtime evidence; resolution: retain the server-only execution boundary.

## BLK-02 — E2E endpoint unavailable — resolved by server-local endpoint

The server-side E2E harness passed with `LENGEAS_E2E_BASE_URL=http://127.0.0.1:8000`, and the public E2E harness now passes with `LENGEAS_E2E_BASE_URL=https://games.lengrowth.com`; both results are recorded in `operations/server-runtime.json`.

Owner: `qa_owner`; status: resolved; resolution: retain both server-local and public E2E checks.

## BLK-03 — Remote repository protection and CI gate — resolved

The remote is configured as `https://github.com/Lengrowth/LenGeas.git`. `main` is protected with strict `verify`, `dependency-review`, and CodeQL matrix checks, linear history, conversation resolution, and no force-push/deletion. The solo-developer policy intentionally requires no approving review and no signed commits. PR #14 verification run `34759754929` passed all required checks.

Owner: `infrastructure_owner`; status: resolved; resolution: transfer to `Lengrowth`, enable dependency graph/alerts, apply the live protection export, and pass the hosted verification workflow.

## BLK-05 — Public DNS/TLS cutover — resolved

`games.lengrowth.com` resolves to `3.238.63.61`. Caddy obtained a valid production certificate, `https://games.lengrowth.com/health` and `/version` return the expected API responses, and public E2E passes. The record is currently DNS-only; Cloudflare proxying can be enabled after this direct-origin validation if desired.

Owner: `infrastructure_owner`; status: resolved; resolution: retain the DNS record and certificate, or optionally enable Cloudflare proxying with Full (strict).

## BLK-04 — Sigstore sample verification — resolved

The keyless release workflow completed for `v0.1.1` in run `34760098397`. Buildx published the image with SBOM/provenance, Cosign signed it using GitHub OIDC, Cosign verified the expected workflow certificate identity and issuer, and the release manifest uploaded successfully. Git commit/tag signatures are not required by the sole-developer branch policy; published container artifacts remain signed.

Owner: `release_manager`; status: resolved; resolution: use the successful `v0.1.1` release evidence and retain the keyless artifact-signing workflow.
