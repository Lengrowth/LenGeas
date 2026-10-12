# Phase 05 implementation decisions

- **Status:** all P05-T01 through P05-T08 are `in_review`; repository-owner acceptance is pending.
- Execution inputs are frozen dataclasses and caller-provided values. Runtime modules do not read the clock, environment, filesystem, network, or unseeded random sources.
- The runtime package stays pure and dependency-light. FastAPI, policy authorization, MongoDB, and event-delivery adapters remain outside it.
- Action planning returns immutable costs/effects/rewards/timers/events. Application repositories own atomic state, receipt, idempotency, and outbox commits.
- The API test application uses a process-local repository. A Mongo transaction adapter is provided separately; a live Mongo-backed API composition and failure-injection run are outside the available local infrastructure.
- The cross-architecture workflow records per-architecture replay and benchmark artifacts. No hosted run or signature is claimed by this local evidence.
