# Phase 02 provider setup

Terraform owns persistent AWS, Cloudflare, MongoDB Atlas, Supabase, and DNS
configuration. Provider credentials are supplied by supported environment or
OIDC integrations and are never placed in Terraform variables, plan files,
state, evidence, or repository configuration.

The repository currently has limited read-only AWS access, authenticated GitHub
access, and no established Cloudflare, Atlas, Supabase, Resend, or Sentry
deployment access. The Phase 02 roots therefore default to disabled and remain
planned-only. The actual Cloudflare plan must be inventoried before enabling
paid WAF, bot, Turnstile, Access, logging, or other optional capabilities.

After the owner resolves the blockers, run the bootstrap roots in dependency
order, import matching existing resources, configure protected OIDC roles, and
record redacted plan/apply evidence. Production data is prohibited in the
exercise environment.
