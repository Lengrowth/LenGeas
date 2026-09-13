# Credential rotation

Secrets are empty Terraform containers referenced by ARN/name. Values are injected by the approved secret operator and never enter variables, plans, state, evidence, logs, or images.

Create a new version, deploy consumers that can read both versions, send a synthetic request, revoke the old version, and verify failure of the old credential. Record only secret names, version labels, timestamps, and result.
