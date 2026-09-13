# Phase 01 security evidence

The local policy scan passed for tracked configuration, exact dependency references, no credentials, no disabled mandatory commands, and no mutable container tags.

Hosted evidence is available and current:

- Verify run `34761194151` passed the hosted Ubuntu test, Trivy filesystem scan, Gitleaks scan, SBOM upload, and all repository policy checks.
- CodeQL run `34761194156` passed Python and JavaScript/TypeScript analysis.
- Dependency review run `34761194157` passed.
- Release run `34760098397` built the `v0.1.1` image with SBOM and SLSA provenance, signed it with keyless Cosign/OIDC, verified the certificate identity, and uploaded the release manifest.

The developer workstation intentionally does not run Docker. Server-side AWS smoke and hosted Ubuntu evidence cover the dependency-backed checks.
