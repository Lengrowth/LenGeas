# Supabase key rotation

Confirm the JWKS endpoint and expected issuer/audience from secret names only. Publish the new asymmetric key with overlap, exercise new and old signatures, unknown-key refresh, invalid signature, and algorithm-confusion rejection, then revoke affected JWT IDs or subject session epochs and clear the verifier cache. Record key IDs and stable error codes only.

Rollback is cache restoration plus provider-side key reactivation during the overlap window. Production provider activation remains deferred by ADR-0011.
