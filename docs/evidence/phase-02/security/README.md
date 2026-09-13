# Phase 02 security evidence

The live development boundary is recorded through read-only EC2/security-group inventory and the Phase 01 loopback-only Compose contract. The public origin, unencrypted root volume, missing instance profile, basic monitoring, restricted SSH, and single-AZ placement are explicit development risks. Customer and production data are prohibited.

Static production-target controls remain in `infrastructure/policies/phase02-controls.json` and are checked by `tools/dev/phase02_checks.py negative`. Live control-plane, origin-denial, PrivateLink, IAM, and secret-rotation evidence is deferred to the ADR-0011 rollout gate.
