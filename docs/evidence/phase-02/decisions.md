# Phase 02 decisions

- The repository owner accepted ADR-0011 on 2026-09-13.
- Adopt `LenGeas-Phase01-Server`, a running `t3.medium` in `us-east-1a`, as the active development foundation.
- Preserve the DNS-only `games.lengrowth.com` endpoint for synthetic development traffic.
- Add no VPC, NAT gateway, ECS capacity, managed database/cache/broker/stream, managed observability, staging, production, or DR resources in Phase 02.
- Retain ADRs 0001–0005 and 0008–0010 as target v1 technology boundaries, not current deployed state.
- Keep production-target Terraform disabled and require a new rollout ADR before any apply.
- Production region choices are candidates to confirm or supersede at rollout; `eu-central-1` and `eu-west-1` do not describe the existing machine.
- Record the current host's unencrypted root volume, missing instance profile, basic monitoring, public origin, single-AZ placement, and restricted SSH as development-only risks. Customer and production data are prohibited.
