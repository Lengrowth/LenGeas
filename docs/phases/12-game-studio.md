# Phase 12 — Game Studio

> AI execution: Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). The Studio uses public platform APIs only.

## Mission

Deliver the complete human control plane for every v1 administrative, authoring, validation, simulation, analytics, support, approval, publishing, and rollback workflow.

## Required reading and entry

Phases 00–11 must be accepted. Read the Phase 11 handoff; ADRs for Cloudflare, OpenNext, Supabase, schemas, and authorization; `08-identity-tenancy-authorization.md`, `10-versioning-publishing-liveops.md`, `12-simulation-balance-experiments-analytics.md`, `13-game-studio.md`, `17-security-and-abuse-prevention.md`, and `19-testing-and-quality-gates.md`.

## Exact output tree

```text
apps/studio/
  app/{dashboard,games,definitions,systems,mechanics,liveops,monetization,simulation,analytics,multiplayer,players,agents,publishing,admin}/
  components/{generated,domain,graphs,forms,layout,feedback}/
  lib/{api,auth,authorization,environment,telemetry,validation}/
  tests/{unit,component,e2e,accessibility,visual,security}/
packages/shared-types/studio/
docs/reference/studio/
docs/runbooks/studio-auth-and-deployment.md
docs/evidence/phase-12/
```

## Tasks

- [ ] **P12-T01 — Application shell and deployment.** Create Next.js 16 App Router, strict TypeScript, Tailwind, shadcn/ui, generated client, TanStack Query, Supabase sessions, Cloudflare Access, CSP/CSRF, environment banner, error boundaries, request IDs, OpenTelemetry, Sentry redaction, OpenNext Worker config, preview and gradual production deployments.
- [ ] **P12-T02 — Tenant administration.** Implement studio/member/role/service-account/game/blueprint/module/environment/integration/owner/audit views. Every button renders from authorization capabilities returned by API; hidden UI never replaces server authorization. Depends on P12-T01.
- [ ] **P12-T03 — Schema authoring.** Generate accessible fields for every v0.1 schema, add domain widgets, immediate local validation, authoritative server validation, draft version, JSON Pointer errors, explicit patches, undo, structured diff, three-way conflict merge, and localization coverage. Depends on P12-T01 and Phase 04 generated types.
- [ ] **P12-T04 — Visual editors.** Implement React Flow progression and story graphs, economy faucet/sink/curve view, timer editor, UTC LiveOps calendar, experiment editor, and module configuration. Persist graph layout only as presentation metadata. Depends on P12-T03.
- [ ] **P12-T05 — Simulation and analytics.** Build run specification, start/cancel, live operation status, result/artifact comparison, balance assertions, saved governed queries, data-quality banners, experiment exposure/results/decision, and cost display. Depends on P12-T01 and Phase 11 APIs.
- [ ] **P12-T06 — Publishing and packages.** Implement freeze, validation stages, migration rehearsal, staging assignment, explicit repository-owner approval, canary metrics, progressive rollout, rollback, signed artifact release report, package install/upgrade/revoke, and exact digest display. Depends on P12-T03 and Phase 08.
- [ ] **P12-T07 — Support and operations.** Implement case-bound redacted player timeline, state/definition pin, receipt/ledger/entitlement/sync/match views, compensating transaction request, quarantine resolution, queue/event/timer health, alert links, and runbook links. Direct state editing is absent. Depends on P12-T02.
- [ ] **P12-T08 — Frontend qualification.** Pass WCAG 2.2 AA, keyboard-only graphs/forms, screen-reader announcements, responsive breakpoints, English localization fallback, current/previous Chrome/Edge/Firefox/Safari, visual regression, CSP/CSRF/XSS checks, and performance budgets.
- [ ] **P12-T09 — Asset, localization, and notification tools.** Implement upload/progress/scan/license/variant/reference/takedown views, localization matrix and ICU preview for every locale, notification template/channel preview, consent/frequency policies, send history, provider health, dead-letter retry, and audit. Depends on P12-T03, P08-T09, P10-T09.

## Route and state rules

Routes use game/environment IDs in URL segments and resolve permissions before data requests. Production pages keep a red banner and production hostname visible. A production mutation requires recent re-authentication, typed reason, exact diff/targets, and server-provided approval policy. Query cache keys include studio, game, environment, API version, and actor. Tokens never enter local storage or logs.

## Mandatory E2E journeys

1. Owner creates studio membership, game, blueprint, and installs exact modules.
2. Designer authors every primitive, resolves validation, handles a concurrent conflict, and freezes a draft.
3. Analyst starts simulations, compares versions, observes failing assertion, and returns to edit.
4. The repository owner stages, explicitly approves, canaries, publishes, observes forced health failure, rolls back, and reconstructs the audit.
5. The repository owner opens a support case, views redacted history, requests compensation, re-authenticates, records the correction reason, executes the compensating transaction, and closes the case.
6. Forbidden-role, cross-studio ID, expired session, revoked permission, stale ETag, Worker failure, and API partial outage all fail safely.
7. Designer uploads an asset through quarantine, observes scan/variant, references it, revokes it, validates locale fallback/RTL/plurals, previews every notification channel, and retries a provider dead letter.

## Gate and handoff

Run Studio unit/component/E2E/accessibility/visual/security tests, generated-client drift, bundle/runtime size budget, Lighthouse performance, and `task phase:gate PHASE=12`. Handoff to Phase 13 includes component APIs, generated schema-field registry, mechanics editor extension interface, simulation/analytics view models, publish flow hooks, deployment/runbook links, and browser/accessibility baselines.

The exit reviewer accepts only when every v1 platform operation is possible through Studio without database, CLI, Terraform, or manual configuration-file access.
