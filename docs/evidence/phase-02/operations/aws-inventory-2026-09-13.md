# Redacted AWS development inventory — 2026-09-13

Read-only inventory was rerun before the Phase 02 scope change. Account IDs, instance IDs, IP addresses, subnet/VPC IDs, and credentials are omitted.

| Property | Observed state |
|---|---|
| Name | `LenGeas-Phase01-Server` |
| Region/AZ | `us-east-1` / `us-east-1a` |
| Instance type | `t3.medium` |
| Lifecycle | running |
| Public address | present |
| Root storage | 40 GiB gp3, unencrypted |
| Instance profile | absent |
| EC2 detailed monitoring | disabled |
| Security groups | one |
| Public ingress | TCP 80 and 443 from IPv4 internet |
| Operator ingress | TCP 22 restricted to one IPv4 `/32` |
| Public health | `https://games.lengrowth.com/health` returned HTTP 200 |
| Public version | `https://games.lengrowth.com/version` returned HTTP 200 |

No Phase 02 production VPC, NAT gateway, ECS cluster, ALB, managed data service, staging environment, production environment, or DR environment was created. The current host is the adopted development foundation under ADR-0011.

The unencrypted volume, public origin, missing instance profile, basic monitoring, and single-AZ placement are documented development risks. Only synthetic, non-sensitive data is allowed.
