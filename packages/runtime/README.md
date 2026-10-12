# Runtime package

Phase 05 implements the pure engine under `src/lengeas_runtime/`.

The evaluator accepts immutable state and a pinned execution context. It resolves only registered
typed state paths, evaluates bounded condition and numeric ASTs, and returns immutable action plans.
It does not mutate input state or perform I/O. The application layer owns authorization,
idempotency, transactions, persistence, and committed event IDs.

The package includes PCG64 v1 with supplied 128-bit seeds. Logical time is always caller supplied.
Default limits match `docs/06-runtime-and-rules.md`; the generated operator and API reference is
`docs/reference/runtime-v1.md`.

Local validation uses `task test:unit -- runtime`, `task test:property -- runtime`, and
`task test:security -- runtime`. Runtime source imports are statically checked for prohibited
adapters and I/O facilities.

