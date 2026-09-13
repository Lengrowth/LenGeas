# Game Studio

## Purpose

The Studio is the human control plane for the same public APIs and schemas used by AI agents. It never writes MongoDB, R2, Cloudflare, or AWS resources directly.

## Stack and hosting

The Studio uses Next.js 16 App Router, TypeScript strict mode, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod adapters generated from canonical schemas, and React Flow for graph editors. It runs on Cloudflare Workers through OpenNext. Cloudflare Access protects the production Studio hostname; Supabase Auth provides application identity and sessions.

## Information architecture

- Dashboard: environment health, active releases, incidents, pending approvals, and budget status.
- Games: blueprint, modules, network mode, channels, SDK configuration.
- Definitions: drafts, structured diff, validation, release history, localization.
- Systems: resources, economy, inventory, progression, quests, achievements, timers, rewards, events.
- Mechanics: package installation, configuration, state ownership, compatibility.
- LiveOps and monetization: events, seasons, offers, experiments, remote overrides, entitlements.
- Simulation: specifications, runs, comparisons, assertions, and artifacts.
- Analytics: governed dashboards, event catalog, data-quality status.
- Multiplayer: queues, matches, ratings, leaderboards, moderation, operational controls.
- Players and support: redacted profile, action receipts, ledger, sync conflicts, compensating workflow.
- AI agents: proposals, tool scopes, run history, diffs, validation, review.
- Publishing: pipeline stages, approvals, canary, rollback, release reports.
- Administration: members, roles, service accounts, audit, retention, integrations.

## Editing model

Forms are schema-generated and enriched with domain-specific editors. Every edit updates a local draft, validates immediately, and submits an explicit patch to the Definition API. The server returns the authoritative draft version and validation report. Concurrent edits use optimistic versioning and a three-way structured merge.

## Visual editors

- Progression editor renders nodes and typed edges, detects cycles and unreachable nodes, and exposes condition/cost/reward panels.
- Economy editor renders faucets, sinks, exchanges, generators, curves, and resource projections from simulation data.
- Story editor renders scenes, dialogue, choices, branch conditions, effects, and localization status.
- LiveOps calendar renders UTC and viewer-local times while storing UTC only.

Graph layout is presentation metadata; it never affects runtime order.

## Safety UX

- Environment color and hostname remain visible on every page.
- Production mutations require re-authentication, reason, preview, and the approvals defined by policy.
- Destructive operations show exact affected IDs and use recoverable archive operations when supported.
- Economy correction displays balanced compensating entries before submission.
- Publishing shows digest, structured diff, simulation status, migrations, and rollback target.
- Support views redact PII and watermark exports with actor and case ID.

## Accessibility and internationalization

The Studio meets WCAG 2.2 AA, supports keyboard operation for all editors, provides a non-canvas tabular graph editor, uses semantic status text in addition to color, and localizes the Studio shell independently from game localization.

## Frontend testing

Component tests cover schema widgets and permissions. Playwright covers authoring, validation, publishing, rollback, support, liveops, simulation, multiplayer operations, AI review, accessibility, and responsive layouts. Contract tests run the generated client against the deployed staging API.

## Deployment

Pull requests deploy isolated Worker previews with a synthetic backend. Merges deploy to development, signed release tags deploy to staging, and production promotion requires approval. Content Security Policy, Subresource Integrity where applicable, dependency scanning, source-map protection, and RUM are mandatory.
