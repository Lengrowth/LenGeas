# Phase 01 Decisions

- The workspace had no recoverable `.git` metadata or ancestor repository. Git was initialized explicitly and the unchanged Phase 00 snapshot was imported at `213f5b7`.
- Historical Phase 00 SHAs remain recorded as prior-environment evidence and were not fabricated or rewritten.
- Python `3.13.5`, Node `22.16.0`, pnpm `11.20.0`, uv `0.11.29`, Terraform `1.15.8`, and go-task `3.53.1` are the exact local pins.
- No architecture boundary or accepted ADR was changed.
- Mandatory external checks fail closed when unavailable; they are not reclassified as passes.
- The repository owner authorized a temporary AWS `t3.medium` server deployment and explicitly directed that Docker run only on the server, never on the developer workstation.
- The private repository source was transferred as a `git archive` of the pushed commit over SSH; no GitHub credential was stored on the host.
- The repository owner stated that signing is not needed for this temporary deployment. The Phase 01 signing requirement remains an explicit open gate until the owner changes the phase contract or supplies authentic Sigstore evidence.
