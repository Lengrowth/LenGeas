# Terraform boundary

The production-target infrastructure is a provider-pinned, opt-in reference foundation. Every root defaults to
`enabled = false`; an operator must provide an approved account inventory and
explicitly enable a root before it can create resources. Provider credentials
are read from the provider's environment integration and never from Terraform
variables, files, plans, or state.

The roots are intentionally separate state boundaries:

- `bootstrap/backend` — encrypted, versioned S3 state and native S3 lockfiles.
- `bootstrap/github-oidc` — short-lived GitHub Actions plan/apply roles.
- `bootstrap/organizations` — account/control-plane adoption boundary.
- `environments/nonproduction`, `staging`, `production`, and `dr` — disabled candidate foundations in `eu-central-1` and `eu-west-1`.

Run `terraform init -backend=false` and `terraform validate` in a root before
enabling it. The environment roots are safe to plan without vendor credentials
while disabled; applies require the owner-approved access and cost gate recorded
in Phase 02 evidence.

ADR-0011 makes the existing `us-east-1a` `t3.medium` the active Phase 02 development foundation. These Terraform roots are not applied or required for Phase 02 acceptance. They must be refreshed against current providers, costed, reviewed by a new rollout ADR, and exercised live before Phase 17 production qualification. Their presence is not evidence that AWS Organizations, ECS, managed data services, staging, production, or DR exist.
