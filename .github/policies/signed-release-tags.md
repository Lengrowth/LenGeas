# Signed release-tag policy

This policy is the repository-local contract for release tags. It does not claim that GitHub tag protection or signing enforcement is currently configured.

## Required tag properties

- Release tags match `v<major>.<minor>.<patch>` and are immutable after publication.
- A release tag is an annotated, cryptographically signed Git tag.
- The signature must verify to the repository owner's configured signing identity in the actual GitHub repository. The identity is intentionally not named here because no owner handle or signing key is available.
- Release automation must verify the tag signature and commit ancestry before publishing artifacts.
- Release artifacts must reference the exact tag, commit SHA, image digest, SBOM digest, provenance record, and evidence manifest digest.
- A tag or artifact that fails verification is rejected; no unsigned fallback is permitted.

## Local verification

Run these commands after a signed tag exists:

```powershell
git tag --format="%(refname:short) %(objecttype) %(objectname) %(subject)" --list "v*"
git tag -v v<major>.<minor>.<patch>
git show-ref --verify --quiet refs/tags/v<major>.<minor>.<patch>
```

The current checkout contains no release tag to verify. The repository has no configured remote, so GitHub tag rules and release evidence cannot be checked locally.

## Enforcement boundary

The desired live controls are represented in [repository-policy.yml](../repository-policy.yml). A repository owner must apply equivalent GitHub rules for `v*` and retain the resulting export when a remote and credentials exist. Do not substitute a guessed account, team, screenshot, or successful external check.
