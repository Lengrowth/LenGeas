# Architecture Decision Records

Phase 00 creates the following records as the owner-approved architectural baseline before implementation. The sole developer/repository owner approves them directly; this phase agent cannot make that decision:

- `0001-cloudflare-aws-responsibility-split.md`
- `0002-mongodb-atlas-document-storage.md`
- `0003-ecs-ec2-container-runtime.md`
- `0004-celery-amazon-mq-background-work.md`
- `0005-msk-domain-event-stream.md`
- `0006-json-schema-definition-contract.md`
- `0007-deterministic-expression-ast.md`
- `0008-nextjs-opennext-cloudflare-workers.md`
- `0009-supabase-auth-internal-identity.md`
- `0010-terraform-github-actions-delivery.md`
- `0011-development-first-infrastructure-activation.md`

Use `../templates/adr.md`. An ADR is not accepted until its validation evidence is attached. The architecture in the main documents remains the required v1 decision unless a later accepted ADR supersedes it.

## Phase 00 review state

All ten records are accepted by the sole developer/repository owner. They document the selections already present in the authoritative architecture and technology standards; they do not supersede those documents. Implementation and production validation remain required at the relevant later-phase gates.

## Later decisions

ADR-0011 is accepted by the repository owner and changes infrastructure activation timing: Phase 02 uses the existing low-cost development host, while the production topology remains a target that must be revalidated by a rollout ADR before Phase 17 production qualification.
