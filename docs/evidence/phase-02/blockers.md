# Phase 02 blockers

- BLK-02-01 AWS organization/control-plane access: the authenticated profile is not in an AWS Organization and cannot administer Organizations, CloudTrail, GuardDuty, Security Hub, or Control Tower. Owner action: provide an approved management-account/bootstrap role or complete the account-control-plane setup and record the inventory.
- BLK-02-02 Vendor access: Cloudflare authentication/capability inventory, Supabase, Resend, Atlas, and Sentry access are unavailable. Owner action: provide scoped provider credentials through supported environment/OIDC integrations and confirm the actual plan capabilities.
- BLK-02-03 Cost approval: no approved recurring monthly ceiling or consolidated vendor sizing exists. Owner action: review the plan-only estimate, set the ceiling, and explicitly authorize the isolated exercise apply; production remains gated separately.
- BLK-02-04 CI delivery identity: GitHub is authenticated, but no Phase 02 Terraform plan/apply workflow or proven OIDC roles exist. Owner action: bootstrap the restricted roles and add the protected environment workflow after BLK-02-01.
