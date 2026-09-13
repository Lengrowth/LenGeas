# Deferred production artifacts

These artifacts are unavailable because ADR-0011 intentionally defers production activation. Their absence does not block the development-foundation phase and must not be converted into a success claim.

| Deferred artifact | Required activation action |
|---|---|
| Enabled production Terraform plans and Infracost | Accept rollout ADR, confirm topology/sizing, establish provider access, and approve cost ceiling. |
| AWS organization/control report | Decide the production account structure and establish organization/security administration. |
| Three-AZ Reachability Analyzer and Atlas PrivateLink | Provision the approved production network and Atlas project, then exercise private success/public failure. |
| Cloudflare ruleset, origin-auth rotation, and direct-origin denial | Confirm plan capabilities and deploy the approved production edge/origin path. |
| Supabase JWKS and Resend DNS/webhook | Activate environment-separated provider projects for the rollout. |
| Managed telemetry, Sentry alert, and trace evidence | Provision the selected production observability stack and exercise a synthetic trace/page. |
| Apply/destroy/recreate/zero-drift | Apply only an approved isolated rollout environment and complete the destructive exercise there. |
| AZ and regional failover | Run during production qualification against the activated topology. |

No customer/player data, credentials, state, account identifiers, or fabricated live-success output is present.
