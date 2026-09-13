# Security policy scan

- `python tools/dev/lint.py`: exit 0.
- `python tools/dev/ci_checks.py workflow-policy`: configured to fail on missing action versions, unsafe permissions, disabled commands, and masked failures.
- `python tools/dev/ci_checks.py terraform-policy`: configured to fail on missing provider pins, resources in Phase 01, or credentials.
- `gitleaks`, Trivy, and CodeQL: workflow configuration exists; no local/remote run is claimed.

