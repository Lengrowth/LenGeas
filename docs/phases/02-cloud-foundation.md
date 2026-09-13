# Phase 02 — Cloud Foundation

## Goal

Provision secure, reproducible non-production, staging, production, and DR foundations before application data exists.

## Entry

Phase 01 is accepted; AWS, Cloudflare, MongoDB Atlas, Supabase, Resend, GitHub, and Sentry organization owners are available.

## Tasks

- [ ] **P02-T01 — Bootstrap AWS organization.** Create accounts, Control Tower guardrails, IAM Identity Center, SCPs, central CloudTrail, Config, GuardDuty, Security Hub, log archive, and budgets. Evidence: control report.
- [ ] **P02-T02 — Bootstrap Terraform state.** Create KMS-encrypted versioned S3 state bucket, native lockfiles, OIDC plan/apply roles, and break-glass procedure. Depends on P02-T01. Evidence: state recovery exercise.
- [ ] **P02-T03 — Provision networks.** Create three-AZ VPCs, subnets, routes, NAT, endpoints, security groups, flow logs, primary/DR peering, and DNS. Depends on P02-T02. Evidence: reachability tests.
- [ ] **P02-T04 — Provision compute plane.** Create ECR, ECS clusters, four EC2 capacity providers, ALB, autoscaling, service discovery, task roles, and SSM management. Depends on P02-T03. Evidence: AZ placement and scale test.
- [ ] **P02-T05 — Provision data plane.** Create Atlas projects/clusters/backups/PrivateLink, Valkey, RabbitMQ, MSK, KMS keys, Secrets Manager, and R2 buckets. Depends on P02-T03. Evidence: private connectivity and failover tests.
- [ ] **P02-T06 — Provision Cloudflare edge.** Configure zone, TLS, WAF, DDoS, bots, Turnstile, rate rules, Access, Edge Gateway skeleton, origin allowlist, Workers environments, R2 bindings, and logs. Depends on P02-T04. Evidence: origin-bypass failure test.
- [ ] **P02-T07 — Provision identity/email projects.** Create environment-separated Supabase Auth projects with asymmetric keys and Resend domains/webhooks. Depends on P02-T02. Evidence: DNS/auth/email validation.
- [ ] **P02-T08 — Provision observability.** Create telemetry collectors, CloudWatch, managed Prometheus/Grafana, tracing, Sentry, alert routing, dashboards, and log retention. Depends on P02-T04–T06. Evidence: synthetic alert trace.
- [ ] **P02-T09 — Prove environment reproduction.** Create and destroy an isolated exercise environment through Terraform, then recreate it with zero drift. Depends on P02-T01–T08. Evidence: signed reproduction report.

## Exit gate

Security and SRE approve private connectivity, origin protection, environment isolation, telemetry, backup configuration, cost alarms, and reproducible Terraform. No production customer data exists.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 01 handoff, ADRs 0001–0005 and 0008–0010, plus architecture, technology, security, SRE, and infrastructure documents.

### Exact outputs

`infrastructure/terraform/bootstrap/{backend,github-oidc,organizations}`; modules for `account-baseline`, `vpc`, `endpoints`, `ecr`, `ecs-cluster`, `ecs-service`, `alb`, `iam`, `kms-secrets`, `atlas`, `valkey`, `amazon-mq`, `msk`, `observability`, `cloudflare-zone`, `cloudflare-worker`, `r2`, `supabase`, and `resend`; environment roots for nonproduction, staging, production, and DR; policies under `infrastructure/policies/`; and failover/origin/state runbooks under `docs/runbooks/`.

Every Terraform module has typed variables/outputs, README, example, `terraform test`, policy tests, cost tags, alarms, and least-privilege IAM. Environment roots compose modules and do not copy resources. Secrets are empty containers referenced by ARN/name; values never enter Terraform state.

### Required scenarios

- Attempt and reject public storage, disabled audit, unencrypted storage, public ECS task, SSH, root container, and cross-account escalation.
- Run Reachability Analyzer and prove ECS-to-Atlas PrivateLink while public Atlas access fails.
- Kill EC2 capacity, trigger managed drain, and verify replacement across AZs.
- Trigger staging Atlas, Valkey, and RabbitMQ failovers; backlog and replay MSK.
- Prove WAF, bot/Turnstile, request-size, rate-limit, origin-auth rotation, and direct-origin denial.
- Create, destroy, and recreate an isolated environment; the post-create plan has zero diff.

Store redacted plans, Infracost, policy results, network diagrams, failover timings, Cloudflare ruleset export, resource/tag inventory, and drift results under `docs/evidence/phase-02/`.

### Handoff to Phase 03

List secret names, non-secret endpoints, JWKS URLs, PrivateLink outputs, task-role conventions, telemetry endpoints, dashboards, alert routes, and test-tenant bootstrap command. Never place secret values in the handoff.
