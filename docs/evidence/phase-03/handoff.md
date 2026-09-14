# Phase 03 handoff

## Status

`in_review` — implementation is complete for P03-T01 through P03-T08 and is awaiting repository-owner review. Phase 03 is not accepted and the pull request must remain open and unmerged.

## Actor and scope types

`packages/domain/authorization/policy.py` defines `Actor`, `ActorKind`, `Resource`, `PolicyRequest`, and `Decision`. `packages/domain/tenancy/models.py` defines `TrustedScope` with actor, studio, optional game, environment, roles, support grant, service-account, AI-agent, and expiry fields.

## Interfaces and persistence

All tenant-owned repository calls require `TrustedScope`; request tenant/game/player fields are never used to construct repository filters after authorization. Mongo index names and collection ownership are in `packages/persistence/mongodb/index_manifest.py`. Required unique indexes are provider+subject, guest device key, studio membership, service client ID, and merge idempotency scope.

## Event identity fields

`packages/domain/audit/events.py` provides event ID, type, UTC occurrence, producer, studio, game, player, correlation, causation, and PII-safe payload fields. Published Phase 03 event types are `identity.guest_created.v1`, `identity.linked.v1`, `identity.merged.v1`, `studio.membership_changed.v1`, and `privacy.requested.v1`.

## Public API and generated references

The versioned FastAPI composition root is `apps/api/app/main.py`. The checked-in OpenAPI 3.1 reference is `packages/schemas/api/v1/openapi.json`; its digest is recorded by the final manifest. Operations cover guests, credential rotation, identity links, merge preview/commit, current account, session revocation, studio administration, service accounts, and privacy workflows.

## Rollout and rollback boundary

No production provider project, paid Cloudflare capability, ECS/VPC/NAT/Atlas/Valkey/MQ/MSK resource, first-party game, or production data was created. Rollback before merge is branch/commit revert. Identity merge has an explicit rollback boundary before irreversible tombstoning; after commit, compensation is an audited domain operation.

## Test tenant and next phase

The exact synthetic test command is `uv run --frozen python tools/dev/task_runner.py test unit identity`; hosted CI must run the Docker-backed unfiltered integration suite. Definition ownership is studio-scoped: owners/admins may administer, designers/developers may draft, AI agents may only read or draft, and no AI agent may approve or publish.

Phase 04 must begin with:

```text
uv run --frozen python tools/dev/task_runner.py phase-gate 03
```

Phase 04 must not assume production Supabase/Turnstile activation, Cloudflare proxying, MongoDB availability on the workstation, or that an external provider subject is a LenGeas primary key.
