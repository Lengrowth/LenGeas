# Phase 06 performance evidence

`tests/performance/phase06/test_value_qualification.py` bounds the generator and
checks deterministic seed-range, count, digest, and aggregate validation. The
qualification runner streams deterministic operations directly into account
aggregates and SHA-256 digests and never retains generated rows.

The manual hosted workflow `.github/workflows/phase-06-qualification.yml`
defines 100 independent partitions of 10,000,000 operations and an aggregate
job that rejects missing/overlapping ranges, incomplete counts, or nonzero
conserved totals. A 2,000-operation two-partition local smoke passed; its
seed ranges, counts, and digests (without raw rows) are in `local-smoke.json`.
The one-billion-operation hosted workflow has not run in this task, so the
Phase 06 exit qualification is still unverified.
