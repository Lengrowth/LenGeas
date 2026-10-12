# Determinism and performance evidence

- `replay-local.json` records 1,000 seeds replayed twice on Windows AMD64 with `pcg64-v1`. The aggregate result is deterministic on this host. The report is unsigned because no owner-managed signing key is configured.
- `runtime-benchmark.json` records 1,000 bounded formula evaluations on the local Windows AMD64 host. The observed maximum was below the declared 50,000 µs per-evaluation budget. This workstation is not the contract's reference CPU, so the result does not establish reference-hardware performance.
- `.github/workflows/verify.yml` defines a GitHub-hosted Ubuntu x86-64/ARM64 matrix and uploads separate replay/benchmark reports. Those jobs remain pending until a hosted run is available.
