# Phase 04 performance evidence

Parser limits cap the source package at 5 MiB, nesting depth at 64, AST nodes at 100,000, string values at 4,096 characters, arrays/objects at 4,096 entries, and formula/condition budgets at declared module limits. Boundary tests cover each limit.

On the Windows development host with Python 3.13.5, the 74 unit/security tests completed in 31.73 seconds. The runtime and validation modules report 85.98% combined line coverage. This is a bounded conformance measurement, not a production runtime throughput claim.
