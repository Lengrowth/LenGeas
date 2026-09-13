# Trust Boundaries

```mermaid
flowchart LR
  untrusted[Untrusted inputs\nclients, definitions, assets, prompts, retrieval data]
  edge[Cloudflare edge policy boundary]
  origin[AWS origin boundary\nALB + ECS private subnets]
  auth[Identity and authorization boundary\nSupabase verification + policy decision point]
  runtime[Pure runtime boundary\nbounded AST + deterministic handlers]
  data[Durable authority boundary\nMongoDB Atlas + R2]
  events[Delivery boundary\noutbox + MSK + RabbitMQ]
  ops[Operator and support boundary\ncase-bound, audited, least privilege]
  ai[AI tool boundary\nshort-lived scope, draft only]
  untrusted --> edge --> origin --> auth --> runtime --> data
  runtime --> events
  ops --> auth
  ai --> auth
  ai -. never direct .-> data
  untrusted -. never direct .-> data
```

Boundary rules:

- No public hostname bypasses Cloudflare.
- Edge policy does not execute canonical game rules.
- Origin services accept only authenticated, authorized requests.
- Definitions and prompts are data, never executable authority.
- AI tools can create or patch drafts, validate, simulate, query governed aggregates, and submit for review; they cannot publish, approve, mutate players, read secrets, or access infrastructure.
- Support access is case-bound, redacted, and audited.
- Durable authorities do not accept direct writes from clients, packages, or consumers outside their owning service boundary.
