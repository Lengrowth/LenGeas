"""Static Phase 02 infrastructure policy checks."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TERRAFORM = ROOT / "infrastructure" / "terraform"
MODULES = {
    "account-baseline",
    "vpc",
    "endpoints",
    "ecr",
    "ecs-cluster",
    "ecs-service",
    "alb",
    "iam",
    "kms-secrets",
    "atlas",
    "valkey",
    "amazon-mq",
    "msk",
    "observability",
    "cloudflare-zone",
    "cloudflare-worker",
    "r2",
    "supabase",
    "resend",
}
ROOTS = {"nonproduction", "staging", "production", "dr"}


def fail(message: str) -> int:
    print(f"FAIL phase02-policy: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("contract", "negative"))
    args = parser.parse_args()
    module_root = TERRAFORM / "modules"
    actual_modules = {path.name for path in module_root.iterdir() if path.is_dir()}
    if missing := sorted(MODULES - actual_modules):
        return fail("missing required modules: " + ", ".join(missing))
    env_root = TERRAFORM / "environments"
    actual_roots = {path.name for path in env_root.iterdir() if path.is_dir()}
    if missing := sorted(ROOTS - actual_roots):
        return fail("missing environment roots: " + ", ".join(missing))
    files = sorted(TERRAFORM.rglob("*.tf"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    if 'required_version = "= 1.15.8"' not in text:
        return fail("Terraform version pin is missing")
    for provider, source, version in (
        ("aws", "hashicorp/aws", "6.62.0"),
        ("cloudflare", "cloudflare/cloudflare", "5.24.0"),
        ("mongodbatlas", "mongodb/mongodbatlas", "2.17.0"),
        ("supabase", "supabase/supabase", "1.10.1"),
    ):
        if source not in text or f'version = "= {version}"' not in text:
            return fail(f"provider pin missing for {provider}")
    for module in sorted(MODULES):
        path = module_root / module
        required = ("main.tf", "variables.tf", "outputs.tf", "README.md", "examples", "tests")
        if missing := [item for item in required if not (path / item).exists()]:
            return fail(f"{module} missing: {', '.join(missing)}")
        if 'resource "terraform_data" "contract"' not in (path / "main.tf").read_text(
            encoding="utf-8"
        ):
            return fail(f"{module} does not expose a contract resource")
    for root in sorted(ROOTS):
        root_text = "\n".join(
            (env_root / root / file).read_text(encoding="utf-8")
            for file in ("main.tf", "versions.tf")
        )
        if "use_lockfile = true" not in root_text:
            return fail(f"{root} root does not enable native S3 lockfiles")
        for module in MODULES:
            if not re.search(rf'source\s*=\s*"\.\./\.\./modules/{re.escape(module)}"', root_text):
                return fail(f"{root} does not compose module {module}")
    if args.check == "negative":
        required_tokens = {
            "public storage": "block_public",
            "disabled audit": "audit",
            "unencrypted storage": "encryption",
            "public ECS task": "no-public-ip",
            "SSH or public bastions": "no-ssh",
            "root containers": "readonlyRootFilesystem",
            "cross-account escalation": "cross-account",
            "broad GitHub OIDC trust": "GitHubActionsRestrictedTrust",
            "public Atlas access": "PrivateLink",
            "missing origin authentication": "origin-authentication",
        }
        for label, token in required_tokens.items():
            if token.lower() not in text.lower():
                return fail(f"negative control is not represented: {label}")
        if re.search(r"(?im)^\s*(?:password|secret|token|api_key)\s*=", text):
            return fail("Terraform contains a secret-like assignment")
        print(
            "PASS phase02-policy: mandatory negative-control vocabulary and secret policy present"
        )
        return 0
    print(
        f"PASS phase02-policy: {len(MODULES)} modules and "
        f"{len(ROOTS)} environment roots compose safely"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
