# Deferred production provider setup

Terraform owns persistent AWS, Cloudflare, MongoDB Atlas, Supabase, and DNS
configuration. Provider credentials are supplied by supported environment or
OIDC integrations and are never placed in Terraform variables, plan files,
state, evidence, or repository configuration.

The repository currently has limited read-only AWS access, authenticated GitHub access, and no established Cloudflare, Atlas, Supabase, Resend, or Sentry deployment access. ADR-0011 does not require those production provider connections during Phase 02. All production-target roots remain disabled and planned-only. The actual Cloudflare and other provider plans must be inventoried at rollout before optional or paid capabilities are selected.

The redacted readiness register is maintained in
`docs/evidence/phase-02/operations/provider-activation-matrix.md`. It records
each provider's plan capabilities, expected data, migration boundary, and
activation owner decision without storing credentials or asserting activation.

Provider access is an activation prerequisite rather than a Phase 02 blocker. When an actual rollout workload exists, accept a rollout ADR, run the bootstrap roots in dependency order, import matching resources, configure protected OIDC roles, and record redacted plan/apply evidence. Production data is prohibited until the production qualification gate passes.
