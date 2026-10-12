# Runtime operations and extension points

- API routes and trusted principal injection: `apps/api/app/runtime_api.py`.
- Planning boundary: `plan_action` returns an immutable plan and explanations without mutating state.
- Commit boundary: `ActionRepository.commit_action` persists state, receipt, idempotency record, and outbox in one unit. The in-memory adapter supports local contract tests; `MongoActionRepository` uses a MongoDB transaction and unique indexes.
- Event consumers use an inbox identity scoped by consumer and event ID. Broker polling, retries, and delivery workers are outside Phase 05.
- Timer plans use caller-supplied logical time and pinned definition digest. Scheduling and timer workers are outside Phase 05.
- Generated interface reference: `docs/reference/runtime-v1.md`.

Live Mongo transactions and deployed API operations remain unverified on this workstation; see `../blockers.md`.
