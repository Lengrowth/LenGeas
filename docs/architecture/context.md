# C4 Context

## Review status

- Phase task: `P00-T03`
- Status: `in_review`
- Source authority: `docs/00-product-charter.md`, `docs/01-principles-and-invariants.md`, `docs/02-system-architecture.md`, `docs/17-security-and-abuse-prevention.md`, `docs/20-infrastructure-and-deployment.md`
- Architecture change: none

LenGeas is a multi-tenant platform for studios, users, players, definitions, runtime actions, operations, simulations, analytics, and governed AI proposals. No client, studio user, or AI agent is trusted to mutate authoritative state directly.

```mermaid
C4Context
  title LenGeas system context
  Person(player, "Player", "Uses a game client to send intent")
  Person(studioUser, "Studio user", "Authors and operates definitions through Studio")
  Person(operator, "Platform operator", "Deploys, observes, supports, and responds to incidents")
  System(lengeas, "LenGeas platform", "Validates definitions, evaluates actions, persists state, publishes events, and governs operations")
  System_Ext(auth, "Supabase Auth", "Authentication and asymmetric JWKS")
  System_Ext(providers, "External providers", "App stores, Resend, SNS, VAPID, and model providers")
  Rel(player, lengeas, "Sends signed/authenticated intent")
  Rel(studioUser, lengeas, "Authors, validates, reviews, and publishes through public APIs")
  Rel(operator, lengeas, "Operates through audited tools and deployment pipelines")
  Rel(lengeas, auth, "Verifies identity and maps provider subject")
  Rel(lengeas, providers, "Uses scoped, idempotent integrations")
```

The platform boundary includes Cloudflare edge controls, the AWS application services, durable data services, event/task infrastructure, R2 artifacts, and the public Definition API. Rendering engines, arbitrary user code, and first-party games are outside the boundary.
