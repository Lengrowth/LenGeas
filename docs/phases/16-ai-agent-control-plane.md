# Phase 16 — AI Agent Control Plane

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). The implementing AI must prove that deployed agents have less authority than the implementing environment.

## Mission

Deliver AI Director, Game Design, Story, Economy, Balance, QA, LiveOps, and Analytics agents that operate only through scoped public platform tools and produce reviewable drafts.

## Required reading and entry

Phase 15 must be accepted. Read its handoff and identity/authorization, publishing, simulation/analytics, Studio, AI control-plane, security, operations, and completion contracts.

## Exact outputs

```text
packages/domain/agents/
apps/api/app/agents/
apps/workers/agent_orchestrator/
packages/schemas/api/v1/agents/
packages/agent-tools/{definitions,validation,simulation,analytics,review}/
packages/agent-evals/{director,design,story,economy,balance,qa,liveops,analytics}/
apps/studio/app/agents/
infrastructure/terraform/modules/agent-control-plane/
tests/{contract,integration,e2e,security,performance}/agents/
docs/runbooks/{agent-kill-switch,agent-data-exposure,agent-cost-runaway}.md
```

## Tasks

- [ ] **P16-T01 — Agent identity and tool gateway.** Issue short-lived actor tokens scoped by studio/game/environment/draft/tool/budget. Expose read schema, read permitted definition, create/patch draft, validate, simulate, compare, query governed aggregates, and submit review. Do not expose publish, approve, production state, player mutation, ledger, secrets, infrastructure, arbitrary URL, shell, or code execution.
- [ ] **P16-T02 — Run orchestration.** Implement run/step state machine, context assembly, provider adapter, prompt digest, retries, cancellation, hard token/tool/time/simulation/cost budgets, redaction, immutable tool log, artifact storage, observability, and global/studio kill switches. Depends on P16-T01.
- [ ] **P16-T03 — AI Director.** Parse approved briefs into schema-targeted work, dependency graph, agent assignments, validation/simulation checkpoints, merge order, unresolved issues, and final structured proposal. It cannot suppress failures or submit when blocking validation remains. Depends on P16-T02.
- [ ] **P16-T04 — Design, Story, and Economy agents.** Author only permitted blueprint/content/formula/localization fields, use stable references, explain every patch, request validation after batches, and attach source/assumption metadata. Depends on P16-T03.
- [ ] **P16-T05 — Balance and QA agents.** Generate pinned simulation specs, interpret governed results, propose bounded changes, create invariant/exploit/regression cases, reproduce seeded defects, and never claim retention/revenue causality from proxy metrics. Depends on P16-T03.
- [ ] **P16-T06 — LiveOps and Analytics agents.** Draft bounded schedules/offers/experiments/rollback, query only saved or policy-approved aggregates, enforce small-cohort suppression, cite dataset partitions/query digest, and respect environment. Depends on P16-T03.
- [ ] **P16-T07 — Studio review.** Show model/version, brief, scopes, tool trace, cost, definition diff, validation, simulations, citations, risks, comments, human edits, submission, and explicit repository-owner approval. Revoking a run prevents future tool calls. Depends on P16-T03–T06.
- [ ] **P16-T08 — Evaluation and red team.** Benchmark schema validity, reference accuracy, brief adherence, target fit, exploit detection, cost, and scope. Attack prompt injection from definitions/retrieval, tool escalation, PII/secret extraction, self-approval, production mutation, arbitrary network/code, cost exhaustion, hallucinated IDs, unsafe formulas, and output smuggling.

## Run-record requirements

Store agent/model/provider versions, system prompt digest, brief, input digests, exact tool scopes, calls/results, redaction decisions, patches, tokens/cost/time, validation/simulation evidence, reviewer actions, and disposition. Production player data is prohibited; evaluation and examples use synthetic data.

## Gate and handoff

Each role passes a versioned evaluation set and all high-risk negative cases. Zero critical/high security findings remain. Kill switches work during active calls and prevent new calls. `task phase:gate PHASE=16` verifies no agent credential can approve, publish, mutate player value, read secrets, or exceed budget. Handoff to Phase 17 lists exact deployed agent versions, eval digests, scopes, provider/data inventory, cost ceilings, dashboards, and kill-switch exercises.
