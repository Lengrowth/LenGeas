# ADR-0008 — Next.js through OpenNext on Cloudflare Workers

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Studio owner; Edge and content delivery owner
- Supersedes: none
- Superseded by: none

## Context

The Studio is a Next.js App Router application with strict TypeScript and must run inside the Cloudflare-owned Studio hosting boundary. Node-only incompatibilities are prohibited.

## Decision

Use Next.js 16 with React, TypeScript strict, Tailwind, shadcn/ui, and OpenNext deployed to Cloudflare Workers. The Studio uses the public Definition API and never writes MongoDB, R2, Cloudflare, or AWS resources directly.

## Consequences

This keeps hosting aligned with the edge boundary and supports previews. It requires compatibility checks for runtime APIs, gradual Worker rollout, CSP/SRI controls, and a migration ADR if the hosting adapter changes.

## Rejected designs

- Node server directly exposed from AWS: rejected because it bypasses the selected Studio hosting boundary.
- Browser direct writes to stores: rejected because the Studio must use public APIs and server-side authorization.

## Validation

OpenNext compatibility, preview deployment, accessibility, contract, security, performance, and gradual rollout tests are required before production rollout.

## Rollout and reversal

Deploy isolated previews, then development, staging, and approved production Worker versions. Roll back to the prior Worker version and API-compatible release when health gates fail.
