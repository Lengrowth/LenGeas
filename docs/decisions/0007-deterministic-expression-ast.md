# ADR-0007 — Bounded deterministic expression AST

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Runtime owner; Security owner
- Supersedes: none
- Superseded by: none

## Context

Definitions need conditions and formulas while the runtime must remain deterministic, resource-bounded, safe from code execution, and independent of wall-clock and unseeded randomness.

## Decision

Use the bounded LenGeas condition and numeric expression ASTs. Limit condition depth to 32 and node count to 256, formula operations to 512, and use explicit variables and approved operators. Reject loops, reflection, system calls, network access, dynamic field access, arbitrary strings, and `eval`.

## Consequences

The AST enables portable evaluation and resource exhaustion controls. It limits authoring expressiveness and requires explicit extension design, canonical numeric handling, and performance tests.

## Rejected designs

- Embedded Python or JavaScript expressions: rejected because arbitrary code and reflection violate the security boundary.
- Unbounded expression evaluation: rejected because execution budgets are mandatory.

## Validation

Golden evaluations, boundary and overflow tests, denial explanations, fuzzing, resource-exhaustion cases, and cross-platform replay are required before production rollout.

## Rollout and reversal

Ship the evaluator behind the schema/runtime compatibility contract. Revert to the prior evaluator only for compatible definitions; semantic changes require a new engine version and migration plan.
