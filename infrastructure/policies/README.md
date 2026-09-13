# Infrastructure policies

Phase 02 policies fail closed on public storage, disabled audit, unencrypted
storage, public ECS task addressing, SSH/public bastions, root containers,
cross-account escalation, broad GitHub OIDC trust, public Atlas access, missing
origin authentication, direct-origin access, and cross-environment state or
credentials. The policy identifiers are consumed by
`tools/dev/phase02_checks.py` and are evidence requirements, not claims that a
live provider integration has already passed.

`phase02-controls.json` is the review inventory. Run
`python tools/dev/phase02_checks.py negative` to verify that the repository
represents every mandatory negative control. Live results belong under
`docs/evidence/phase-02/security/`.
