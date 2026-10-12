# Security evidence

`task test:security -- runtime` passed the AST-based dependency-boundary scan for the runtime package. It rejects imports or use of web frameworks, persistence/broker clients, filesystem, environment, network, wall clock, and non-seeded random facilities.

The local API E2E suite passed trusted-principal authorization, viewer denial, cross-game access denial, server-resolved action definitions, idempotency replay/conflict, and stale-version rejection. The hosted/deployed E2E suite was not run because its URL and credentials are unavailable; see `../blockers.md`.
