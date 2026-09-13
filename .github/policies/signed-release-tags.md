# Signed release-tag policy

This policy is the repository-local contract for release tags. It does not claim that GitHub tag protection or signing enforcement is currently configured.

## Required release properties

- Release tags match `v<major>.<minor>.<patch>` and are immutable after publication.
- A release tag is annotated. Git tag signatures are intentionally not required for this sole-developer repository.
- Release automation signs the published container keylessly with Sigstore and verifies its certificate identity and OIDC issuer before the release manifest is uploaded.
- Release artifacts must reference the exact tag, commit SHA, image digest, SBOM digest, provenance record, and evidence manifest digest.
- A published artifact that fails verification is rejected; no unsigned artifact fallback is permitted.

## Local verification

Run these commands after a signed tag exists:

```powershell
git tag --format="%(refname:short) %(objecttype) %(objectname) %(subject)" --list "v*"
git tag -v v<major>.<minor>.<patch>
git show-ref --verify --quiet refs/tags/v<major>.<minor>.<patch>
```

The current release tag `v0.1.1` is annotated. Its container signature was verified by the GitHub Actions release run recorded in the Phase 01 evidence.

## Enforcement boundary

The live controls are represented in [repository-policy.yml](../repository-policy.yml). Commit and tag signatures are not merge prerequisites; the release workflow remains the enforcement boundary for signed published artifacts.
