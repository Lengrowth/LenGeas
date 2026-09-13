# Infrastructure and Deployment

## AWS accounts and region

AWS Organizations contains `management`, `security`, `log-archive`, `shared-services`, `nonproduction`, `staging`, and `production` accounts. AWS Control Tower guardrails, organization CloudTrail, GuardDuty, Security Hub, AWS Config, central log archive, IAM Identity Center, budgets, and SCPs apply from Phase 02.

Primary production region is `eu-central-1`.

Disaster recovery region is `eu-west-1`. Workloads span three availability zones in the primary region.

## Network

Each environment VPC has public ALB subnets, private application subnets, and isolated data/endpoint subnets across three AZs. ECS tasks have no public IP. NAT gateway and route table are AZ-local. VPC endpoints cover AWS control services. Atlas connects through PrivateLink. Security groups reference other security groups wherever possible.

The ALB accepts HTTPS from Cloudflare address ranges. Administrative access uses Cloudflare Access and AWS Systems Manager; SSH and public bastions are forbidden.

## Compute

ECS clusters use separate EC2 capacity providers:

- `general`: `m7g.xlarge` On-Demand baseline plus Spot burst for stateless workers;
- `simulation`: `c7g.2xlarge` mixed On-Demand/Spot with checkpointable jobs;
- `realtime`: `c7g.xlarge` On-Demand only;
- `critical-workers`: `m7g.large` On-Demand only.

Auto Scaling groups use the ECS-optimized Amazon Linux 2023 ARM64 AMI and managed instance draining. API, realtime, match, scheduler, and critical consumers place at least one task per AZ. Container filesystems are read-only, root users are forbidden, and task roles are service-specific.

## Data services

- MongoDB Atlas dedicated production cluster in AWS `eu-central-1`, three electable nodes across availability zones, encryption, audit, PrivateLink, continuous backup, and tested `eu-west-1` restore.
- ElastiCache for Valkey 8 replication groups use TLS, ACLs, Multi-AZ, automatic failover, and separate logical clusters for cache versus realtime ephemeral state.
- Amazon MQ RabbitMQ uses Multi-AZ cluster deployment and private endpoints.
- Amazon MSK Serverless uses private networking, IAM authentication, TLS, topic policies, and monitored retention.
- R2 buckets are private and separated by data class and environment.
- R2 asset storage uses separate quarantine and approved buckets. R2 Event Notifications feed a Cloudflare Queue; the authenticated consumer invokes the AWS asset worker. Cloudflare Images serves approved raster variants.
- Analytics uses Cloudflare Pipelines into R2 Data Catalog Iceberg tables and R2 SQL through the governed query API. Raw export and catalog-rebuild procedures are mandatory because these Cloudflare analytics services are beta at the architecture baseline.

## Terraform

`infrastructure/terraform/bootstrap` creates the versioned KMS-encrypted S3 state bucket and CI roles through a controlled bootstrap process. Every environment uses a separate state key and `use_lockfile = true`. Providers are pinned. Plans run on pull requests; applies run from protected GitHub environments after approval. Nightly plans detect drift.

Reusable modules cover accounts/guardrails, network, ECS cluster/service, ALB, ECR, IAM, KMS/secrets, Atlas/PrivateLink, Valkey, RabbitMQ, MSK, observability, Cloudflare zone/Workers/R2/WAF, Supabase configuration, and Resend DNS.

## CI/CD

1. GitHub Actions checks source, schemas, tests, Terraform, SBOM, vulnerabilities, and provenance.
2. Docker BuildKit creates ARM64 images and pushes immutable digests to ECR.
3. Keyless signing binds image, source commit, workflow, and SBOM.
4. Staging deploys by digest and runs migrations in expand mode.
5. Smoke and canary tests pass, followed by soak.
6. Production approval promotes the same digest.
7. ECS blue/green deployment shifts 1%, 10%, 50%, and 100% traffic against health gates.
8. Failure returns traffic to the prior task set. Contract-compatible database changes remain.
9. Cloudflare Worker deployment uses versioned gradual rollout and the same release record.

## Cost control

Every resource has owner, environment, service, cost-center, and data-class tags. AWS Budgets and Cloudflare usage alerts page on forecast thresholds. Simulation jobs enforce per-studio quotas and Spot interruption checkpoints. Idle non-production services scale to documented minimums. Production capacity never relies exclusively on Spot.

## Infrastructure acceptance

Terraform can create a new staging environment from empty accounts, deploy all services, run smoke tests, destroy the isolated exercise environment, and reproduce it without manual console changes. Disaster recovery is provisioned and tested from the same modules.
