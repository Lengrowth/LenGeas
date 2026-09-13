# LenGeas Phase Agent Prompt

Implement Phase `<XX>` from `docs/phases/<phase-file>.md`.

Follow `docs/phases/AI-EXECUTION-PROTOCOL.md` exactly. Read all required documents and the accepted prior-phase handoff before editing. Work only within this phase's scope and exact artifact manifests. Do not change architecture, weaken gates, create a game, leave placeholders, or claim acceptance.

For each task:

1. State the task ID being executed.
2. Inspect dependencies and current code.
3. Implement required artifacts and interfaces.
4. Add every named positive, negative, failure, security, and performance test.
5. Run the specified repository commands.
6. Store evidence under `docs/evidence/phase-<XX>/tasks/`.
7. Update contracts, generated reference, runbooks, and traceability in the same change.
8. Mark the task `in_review` only when evidence validates.

At phase end, run `task verify`, `task phase:gate PHASE=<XX>`, and `task evidence PHASE=<XX>`. Create `manifest.json` and `handoff.md`. Report completed task IDs, failed gates, exact blockers, artifact digests, and the first command for the next phase. Do not mark the phase `accepted`; only the repository owner records that explicit decision. No second person or signature is required.
