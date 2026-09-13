# Terraform boundary

Phase 02 is a provider-pinned, opt-in cloud foundation. Every root defaults to
`enabled = false`; an operator must provide an approved account inventory and
explicitly enable a root before it can create resources. Provider credentials
are read from the provider's environment integration and never from Terraform
variables, files, plans, or state.

The roots are intentionally separate state boundaries:

- `bootstrap/backend` — encrypted, versioned S3 state and native S3 lockfiles.
- `bootstrap/github-oidc` — short-lived GitHub Actions plan/apply roles.
- `bootstrap/organizations` — account/control-plane adoption boundary.
- `environments/nonproduction`, `staging`, `production`, and `dr` — composed
  foundations in `eu-central-1` and `eu-west-1`.

Run `terraform init -backend=false` and `terraform validate` in a root before
enabling it. The environment roots are safe to plan without vendor credentials
while disabled; applies require the owner-approved access and cost gate recorded
in Phase 02 evidence.
