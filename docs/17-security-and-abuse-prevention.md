# Security and Abuse Prevention

## Security model

LenGeas uses zero implicit trust across public clients, Studio users, services, packages, agents, cloud accounts, and environments. Authorization is server-side, least-privileged, scoped to tenant and game, and audited.

## Edge and origin

The controls below are production requirements. During the ADR-0011 development stage, `games.lengrowth.com` is a documented DNS-only direct-origin exception on a single host with no customer or production data. It must be labeled development, must not expose its dependency services, and cannot satisfy a production security gate. Production traffic cannot begin until Cloudflare proxy/origin authentication and direct-origin denial are live-tested.

- Cloudflare DNS proxy, DDoS protection, managed WAF, custom rules, bot controls, Turnstile, request-size limits, and rate limits protect every public hostname.
- The AWS origin uses TLS and accepts only Cloudflare source ranges plus an authenticated rotating origin header.
- A scheduled job updates Cloudflare address ranges in AWS security groups and alerts on drift.
- The origin DNS name is not published and direct-origin probes must fail.
- Cloudflare API Shield validates client certificates for privileged machine endpoints after Phase 17 rollout.

## Application security

- Pydantic rejects unknown input fields and enforces byte, list, depth, and numeric limits.
- All database queries derive tenant scope from authorization context.
- Object-level authorization is tested for every route.
- Idempotency protects all value-changing commands.
- SSRF uses a default-deny outbound allowlist and private-address blocking.
- Uploaded files are quarantined, type-sniffed, scanned, size-limited, and re-encoded where applicable before publication.
- Browser controls include CSP, HSTS, secure cookies, CSRF protection, frame restrictions, and dependency integrity.

## Secrets and keys

Secrets live in AWS Secrets Manager or Cloudflare Secrets Store, encrypted by environment-specific keys. ECS task roles replace static AWS credentials. GitHub Actions assumes deployment roles through OIDC. R2 tokens are bucket- and permission-scoped. Rotation cadence is 90 days, with immediate rotation for exposure. Signing and encryption keys have versioned rollover procedures.

## Supply chain

- Dependencies and images are pinned by digest or lockfile.
- Renovate/Dependabot opens controlled updates.
- CI produces SBOMs, runs SAST, secret scanning, dependency and container vulnerability scans, signs images with keyless Sigstore, and stores provenance.
- ECS deployment verifies signature and approved ECR repository.
- Critical exploitable vulnerabilities block release; production remediation SLA is 24 hours.

## Economy and purchase integrity

App-store receipts are verified with the provider server API. Webhook and polling reconciliation handle delayed state. Grant uses provider transaction ID as a permanent idempotency key. Refund and chargeback create entitlement revocation or debt policy actions; they never edit ledger history.

Fraud signals include impossible action rate, definition mismatch, replay, clock manipulation, device farms, payment anomalies, collusion, duplicate provider IDs, and ledger imbalance. Automated controls quarantine value and create a review case; they do not silently delete value.

## Data protection

Data is encrypted in transit and at rest. PII is isolated, field-encrypted where required, minimized, classified, retained by schedule, and excluded from logs/events/analytics. Support access is case-bound. Export and deletion workflows are verified end to end.

The current development host predates the production storage baseline and has an unencrypted root volume. Only synthetic, non-sensitive development data is permitted there. Production activation requires encrypted storage and a migration that does not copy development secrets or data into production.

## Security testing

Required gates include threat models, authorization matrices, SAST/DAST, API fuzzing, dependency/container scans, IaC scanning, secret scanning, tenant-escape tests, replay/idempotency tests, formula resource-exhaustion tests, file-upload tests, multiplayer abuse tests, and an independent penetration test before v1 completion.

## Incident response

Severity definitions, 24/7 paging for Sev-1, evidence preservation, containment, key rotation, customer communication, recovery, and post-incident review have exercised runbooks. The security lead owns the incident program.
