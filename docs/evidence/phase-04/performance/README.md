# Phase 04 performance evidence

Parser limits cap the source package at 5 MiB, nesting depth at 64, AST nodes at 100,000, string values at 4,096 characters, arrays/objects at 4,096 entries, and formula/condition budgets at declared module limits. Boundary tests cover each limit.

On the Windows development host with Python 3.13.5, the 74 unit/security tests completed in 32.52 seconds. The runtime and validation modules report 85.98% combined line coverage. This is a bounded conformance measurement, not a production runtime throughput claim. The generated TypeScript validator's runtime vectors are executed separately by `task typecheck`.

Fresh local smoke on 2026-10-12 reran the recorded unit/security suite: 74 passed in 33.13 seconds on Python 3.13.5 / Windows, with 85.9797% combined line coverage. Machine-readable run details are in local-smoke.json; this is bounded conformance evidence, not a production throughput claim.
