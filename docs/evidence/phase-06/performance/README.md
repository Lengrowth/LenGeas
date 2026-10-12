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

The hosted one-billion-operation qualification passed on 2026-10-12 in
[GitHub Actions run 38252037777](https://github.com/Lengrowth/LenGeas/actions/runs/38252037777)
against commit `a34f47b32961e351843d9755eeeeefe852c0f6ca`. The aggregate
validated 100 contiguous ranges of 10,000,000 operations each, 1,000,000,000
operations total, and zero conserved-value imbalance. The aggregate digest and
per-partition operation/seed ranges, counts, and SHA-256 digests are recorded in
`hosted-qualification.json`; raw generated operations were not retained.
