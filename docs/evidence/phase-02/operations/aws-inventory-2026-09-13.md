# Redacted AWS inventory — 2026-09-13

Read-only inventory was run before any Phase 02 mutation.

| Scope | Observed state |
|---|---|
| `eu-central-1` EC2 | No instances; no ECS clusters, ALBs, or NAT gateways observed. |
| `eu-central-1` VPC | Only the default VPC was observed. |
| `us-east-1` EC2 | Existing instances include the Phase 01 server (`t3.medium`) and other pre-existing hosts. |
| `us-east-1` VPC | Existing non-default `lenos-vpc` plus the default VPC. |
| AWS Organizations | `AWSOrganizationsNotInUseException`; the account is not in an Organization. |
| AWS Budgets | Read denied for the current IAM user; no budget inventory was captured. |

Instance IDs, account IDs, credentials, state, and secret values are omitted.
The Phase 01 host and its direct-origin path were not changed. The required
Phase 02 three-AZ/network/managed-service design cannot safely be installed on
that host; AWS foundation capacity and organization bootstrap therefore remain
an explicit gate.
