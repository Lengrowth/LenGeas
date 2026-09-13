# Phase 02 decisions

- Preserve the accepted AWS/Cloudflare/Atlas/ECS/MQ/MSK/OpenNext/Supabase/Terraform ADRs; no technology boundary changed.
- Use disabled-by-default modules and separate state roots so code, plans, and policy checks can proceed without fabricating provider applies.
- Keep Resend as DNS/webhook configuration without inventing a provider; secret values remain external.
- Treat missing required vendor access and missing cost approval as mandatory blockers, not as successful planned infrastructure.
- Preserve the temporary Phase 01 direct-origin endpoint until an owner-authorized Cloudflare cutover is verified.
