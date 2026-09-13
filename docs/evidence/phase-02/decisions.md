# Phase 02 decisions

- Preserve the accepted AWS/Cloudflare/Atlas/ECS/MQ/MSK/OpenNext/Supabase/Terraform ADRs; no technology boundary changed.
- Use disabled-by-default modules and separate state roots so code, plans, and policy checks can proceed without fabricating provider applies.
- Keep Resend as DNS/webhook configuration without inventing a provider; secret values remain external.
- Record the owner-approved envelope: Cloudflare and Atlas up to USD 500/month, Supabase and Resend basic plans, and no additional AWS machine capacity. Cost authorization does not substitute for provider credentials, AWS organization bootstrap, or live evidence.
- Treat missing required vendor access and unresolved AWS foundation scope as mandatory blockers, not as successful planned infrastructure.
- Preserve the temporary Phase 01 direct-origin endpoint until an owner-authorized Cloudflare cutover is verified.
