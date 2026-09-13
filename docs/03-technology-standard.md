# Technology Standard

This document records the selected v1 stack. A replacement requires an accepted ADR.

## Application stack

| Area | Selected technology | Binding decision |
|---|---|---|
| Backend language | Python 3.13 | One minor version across local, CI, and production |
| API | FastAPI, Pydantic 2, Uvicorn | REST/OpenAPI 3.1 and WebSocket ingress |
| Dependency and build tool | `uv` | Locked dependencies and Python workspaces |
| Lint/type/test | Ruff, mypy strict, pytest | CI blocks merge on failure |
| Primary database | MongoDB Atlas dedicated clusters on AWS | Motor-compatible async driver through the current PyMongo async API selected during Phase 01 lock-in |
| Cache/ephemeral state | Amazon ElastiCache for Valkey 8 | Redis protocol, TLS, Multi-AZ, automatic failover |
| Background tasks | Celery 5.6 | Managed RabbitMQ broker; Valkey result backend with expiring results |
| Task broker | Amazon MQ for RabbitMQ, Multi-AZ cluster | Durable quorum queues for value-sensitive work |
| Domain events | Amazon MSK Serverless | Kafka-compatible durable event stream and replay |
| Frontend | Next.js 16, React, TypeScript strict, Tailwind CSS, shadcn/ui | App Router; deployed to Cloudflare Workers with OpenNext |
| JavaScript workspace | pnpm workspaces and Turborepo | One lockfile and cached task graph |
| Authentication | Supabase Auth | Asymmetric signing keys, email plus Apple and Google providers |
| Transactional email | Resend | React Email templates and webhook reconciliation |
| Schema | JSON Schema Draft 2020-12 | Canonical definition contract; generated Python and TypeScript types |
| API description | OpenAPI 3.1 | Generated from FastAPI and diff-checked in CI |
| Object storage | Cloudflare R2 | S3-compatible private buckets |
| Analytics lake | Cloudflare Pipelines, R2 Data Catalog, R2 SQL | HTTP/Worker ingestion to Apache Iceberg in R2 and governed SQL queries |
| Image delivery | Cloudflare Images | Approved raster variants and transformation controls |
| Mobile push | Amazon SNS Mobile Push | APNs and FCM delivery from one notification service |
| Containers | Docker BuildKit | Non-root, read-only filesystem, multi-stage ARM64 images |
| Container orchestration | Amazon ECS on EC2 capacity providers | Graviton Auto Scaling groups across three AZs |
| Infrastructure as code | Terraform | Remote encrypted S3 state with `use_lockfile = true` |
| CI/CD | GitHub Actions with OIDC | No long-lived AWS or Cloudflare deployment keys in GitHub |
| Repository task runner | go-task `Taskfile.yml` | Cross-platform commands for bootstrap, generation, tests, evidence, and phase gates |
| Source control | GitHub | Protected trunk, required checks, CODEOWNERS |
| Observability | OpenTelemetry, Amazon Managed Service for Prometheus, Amazon Managed Grafana, CloudWatch Logs, AWS X-Ray | One trace context from edge through workers and event consumers |
| Error tracking | Sentry | Server and Studio exceptions with PII scrubbing |
| Secrets | AWS Secrets Manager, AWS KMS, Cloudflare Secrets Store | Environment-separated secrets and automated rotation |

## Infrastructure standard

- Terraform creates all persistent cloud resources. Console-only resources fail the drift check.
- Amazon Linux 2023 ECS-optimized ARM64 AMIs run ECS capacity. AWS Systems Manager replaces SSH.
- The API and general workers use `m7g` instances. Simulations use `c7g` instances. Real-time matches use `c7g` instances on a dedicated capacity provider.
- ECS managed scaling maintains spare capacity for one availability-zone loss.
- AWS ALB handles HTTP/2, WebSockets, health checks, and target routing.
- NAT gateways exist per availability zone. Interface VPC endpoints cover ECR, CloudWatch, Secrets Manager, KMS, SSM, and STS.
- MongoDB Atlas production starts as a dedicated three-node replica set distributed across AWS availability zones in `eu-central-1`. Continuous cloud backup and point-in-time restore are enabled. DR uses a tested restore target in `eu-west-1`.
- R2 uses separate buckets for published definitions, user assets, simulation artifacts, analytics, and audit exports. Object versioning and lifecycle policies are environment-specific.

## Cloudflare standard

- Cloudflare manages authoritative DNS, Universal SSL, WAF managed rules, DDoS protection, Bot Management, Turnstile, API rate limiting, cache rules, origin rules, Workers, Queues for edge-only buffering, and R2.
- Cloudflare Pipelines writes analytics to R2 Iceberg tables registered in R2 Data Catalog; R2 SQL powers the governed query adapter. Phase 10 pins the beta feature versions and must pass export/recovery tests before completion.
- `studio.lengeas.com` runs Next.js through OpenNext on Workers. OpenNext is selected because the currently documented vinext path is beta; migration requires an ADR after compatibility and production-readiness review.
- `api.lengeas.com/*` executes the Edge Gateway Worker before reaching AWS.
- Definition and asset downloads use signed, short-lived Worker URLs backed by private R2 buckets.
- Cloudflare state never becomes canonical player economy or match state.

## Version policy

Major and minor versions named above are the baseline. Phase 01 records exact patch versions in lockfiles and container base-image digests. Dependabot opens weekly patch updates. Minor updates require full CI and staging soak. Major updates require an ADR and migration plan.

## Decision evidence

- Cloudflare Workers routes are designed to execute in front of an application origin: <https://developers.cloudflare.com/workers/configuration/routing/routes/>.
- Cloudflare documents R2 as S3-compatible object storage: <https://developers.cloudflare.com/r2/get-started/s3/>.
- Cloudflare documents the OpenNext adapter and its supported Next.js features: <https://developers.cloudflare.com/workers/framework-guides/web-apps/opennext/>.
- Cloudflare documents Pipelines delivery to R2 as Parquet/Iceberg and R2 SQL over the R2 Data Catalog: <https://developers.cloudflare.com/pipelines/> and <https://developers.cloudflare.com/r2-sql/>.
- AWS documents EC2 Auto Scaling group capacity providers for ECS: <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/asg-capacity-providers.html>.
- MongoDB documents Atlas private endpoints over AWS PrivateLink: <https://www.mongodb.com/docs/atlas/security-private-endpoint/>.
- Celery documents RabbitMQ as a stable broker and Redis-compatible storage as a result backend: <https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/>.
- Terraform documents S3 native lockfiles and bucket versioning: <https://developer.hashicorp.com/terraform/language/backend/s3>.
