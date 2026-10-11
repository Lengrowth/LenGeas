# Authorization matrix

The centralized policy service evaluates actor kind, tenant, game, ownership, environment, support case, time-bound grant, MFA, service scopes, and AI-agent restrictions. Allow/deny explanations use stable codes: `allow`, `tenant_mismatch`, `role_denied`, `ownership_required`, `support_grant_expired`, `support_case_required`, `mfa_required`, `service_scope_missing`, and `ai_publish_forbidden`.
