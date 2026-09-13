# Cloudflare edge incident

The incident commander declares the edge state and keeps the AWS origin private. Do not bypass Cloudflare or publish the origin hostname. Preserve WAF/rate/origin-auth exports and synthetic trace IDs.

If a Worker regression is isolated, roll back to the prior version. If Cloudflare is unavailable, follow the declared degraded-mode decision and owner approval; direct-origin exposure is forbidden. Restore normal routing only after authenticated origin and edge protections are verified.
