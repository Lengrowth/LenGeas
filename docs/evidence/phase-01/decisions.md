# Phase 01 Decisions

- The workspace had no recoverable `.git` metadata or ancestor repository. Git was initialized explicitly and the unchanged Phase 00 snapshot was imported at `213f5b7`.
- Historical Phase 00 SHAs remain recorded as prior-environment evidence and were not fabricated or rewritten.
- Python `3.13.5`, Node `22.16.0`, pnpm `11.20.0`, uv `0.11.29`, Terraform `1.15.8`, and go-task `3.53.1` are the exact local pins.
- No architecture boundary or accepted ADR was changed.
- Mandatory external checks fail closed when unavailable; they are not reclassified as passes.
- The repository owner authorized a temporary AWS `t3.medium` server deployment and explicitly directed that Docker run only on the server, never on the developer workstation.
- The private repository source was transferred as a `git archive` of the pushed commit over SSH; no GitHub credential was stored on the host.
- The repository owner stated that commit and tag signing is not needed for this temporary deployment. The published container artifact still uses the Phase 01 keyless Sigstore path, and authentic verification evidence was produced by the `v0.1.1` release run.
- The repository was transferred to the `Lengrowth` organization. The sole-developer branch policy requires CI/CodeQL, linear history, conversation resolution, and force-push/deletion protection, but intentionally requires no approving review, signed commit, or signed Git tag. Published container artifacts remain keylessly signed and verified by the release workflow.
- Hosted verification run `34759754929` and keyless release run `34760098397` provide the external CI and Sigstore evidence for this review candidate.
- The repository owner is the sole developer and approval authority. Role IDs are responsibility labels only. No second reviewer, committee, CODEOWNER approval, signed commit, or signed Git tag is required. Automated gates, keyless artifact verification, evidence, and explicit owner decisions remain required.
- The review candidate uses intentional two-commit evidence semantics: source-document commit `31235eaa904c1cd45102e7c35fe702cbb5a10565` remains the manifest `final_commit`, while subsequent commits contain evidence-only review remediation. Evidence-only commits must not be treated as new source implementation commits.
- `task evidence PHASE=01` and `python tools/dev/evidence.py 01` are read-only verification commands. The only manifest writer is the explicit `python tools/dev/evidence.py 01 --regenerate` path; it preserves the committed source-document `final_commit`, regenerates deterministic LF-normalized artifact digests, then reads the manifest back for validation.
- Live repository settings were corrected during review: required pull-request approvals are `0`, required commit signatures are disabled, squash merge is enabled, and merge-commit/rebase merge methods are disabled.
