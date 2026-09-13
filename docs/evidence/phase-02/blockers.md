# Phase 02 blockers

No mandatory blocker remains under the ADR-0011 development-first scope.

The following are deferred production activation prerequisites, not Phase 02 blockers:

- Accept a rollout ADR based on the actual workload, capacity, security, data-residency, migration, and rollback requirements.
- Confirm or supersede the candidate `eu-central-1` primary and `eu-west-1` DR regions.
- Approve a current consolidated production cost ceiling.
- Establish required AWS Organizations and provider administration.
- Configure restricted GitHub OIDC delivery roles and encrypted remote Terraform state.
- Provision and live-test Cloudflare origin protection, ECS, managed data, identity/email, observability, backup, failover, and DR.

None of those capabilities is claimed as current infrastructure.
