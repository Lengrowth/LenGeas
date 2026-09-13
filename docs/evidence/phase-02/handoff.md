# Phase 02 Handoff

## Status

blocked — the repository contains a fail-closed Terraform foundation and review evidence. The owner has approved a vendor cost envelope, but required provider credentials, AWS Organizations bootstrap, and reconciliation of the no-new-AWS-machine constraint are still unavailable. This is not an acceptance record and no Phase 02 resource apply is claimed.

## Operational state

No Phase 02 persistent resource was applied. The Phase 01 us-east-1 EC2 host and DNS-only games.lengrowth.com endpoint remain untouched and temporary. A read-only AWS inventory is recorded in `operations/aws-inventory-2026-09-13.md`; the four environment roots default to enabled = false, with primary eu-central-1 and DR eu-west-1.

## Interfaces and conventions

Provider pins are AWS 6.62.0, Cloudflare 5.24.0, MongoDB Atlas 2.17.0, Supabase 1.10.1, and Terraform 1.15.8. Secret values are never Terraform variables/state; only secret names/ARNs are defined. Backend keys are environment-specific and use native S3 lockfiles.

## Planned-only resources

AWS Organizations/control plane, backend state bucket, OIDC roles, VPC/ECS/data/observability, Cloudflare edge/R2, Supabase, Resend, and reproduction resources are planned-only pending provider access and AWS-scope resolution. The owner authorization is recorded in `operations/owner-authorization.md`; no customer/player data exists in Phase 02.

## First command after unblock

uv run --frozen python tools/dev/task_runner.py phase-gate 02

## Prohibited assumptions

Do not treat static Terraform validation as live evidence; do not run Docker locally; do not expose or retire the Phase 01 origin; do not publish origin names; do not apply production or create recurring-cost resources outside the recorded owner envelope and approved exercise scope.
