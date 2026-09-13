# ADR-0010 — Terraform and GitHub Actions delivery

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Infrastructure owner; Engineering owner
- Supersedes: none
- Superseded by: none

## Context

All persistent resources must be reproducible, reviewed, drift-checked, and deployed without long-lived credentials or console-only steps. Releases need immutable artifacts, provenance, and environment approvals.

## Decision

Use Terraform for AWS, Cloudflare, MongoDB Atlas, Supabase configuration, and Resend DNS records. Use a versioned KMS-encrypted S3 backend with `use_lockfile = true`. Use GitHub Actions with OIDC to assume protected deployment roles; plans run in pull requests and applies run only from protected environments.

## Consequences

The workflow gives reviewable infrastructure, short-lived credentials, and reproducible delivery. It requires bootstrap controls, state recovery, provider pinning, OIDC trust review, drift detection, and release evidence.

## Rejected designs

- Console-only resource creation: rejected because it cannot satisfy drift-free reproducibility.
- Long-lived CI access keys: rejected because OIDC and short-lived roles are required.

## Validation

Empty-account staging reproduction, plan/apply approval, drift detection, state-lock recovery, OIDC trust, secret scanning, signed artifact, and destroy-isolated-exercise tests are required before production rollout.

## Rollout and reversal

Bootstrap state and roles under controlled review, then provision development, staging, and production independently. Revert to a prior immutable plan and release record; state rollback is performed only through an approved recovery procedure.
