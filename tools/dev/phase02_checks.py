"""Static Phase 02 infrastructure policy checks."""

from __future__ import annotations

import argparse
import json
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
CONTROL_INVENTORY = ROOT / "infrastructure" / "policies" / "phase02-controls.json"


def fail(message: str) -> int:
    print(f"FAIL phase02-policy: {message}", file=sys.stderr)
    return 1


def negative_control_checks(text: str) -> dict[str, bool]:
    """Return one fail-closed structural result for every inventory control."""
    lower = text.lower()
    roots = [TERRAFORM / "environments" / name / "versions.tf" for name in sorted(ROOTS)]
    backend_keys = [
        re.findall(r'key\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8")) for path in roots
    ]
    return {
        "P02-NEG-001": "block_public_acls" in lower and "restrict_public_buckets" in lower,
        "P02-NEG-002": all(
            token in lower for token in ("cloudtrail", "guardduty", "securityhub", "config")
        ),
        "P02-NEG-003": all(
            token in lower for token in ("server_side_encryption", "kms_key", "enable_key_rotation")
        ),
        "P02-NEG-004": "assign_public_ip = false" in lower and "no-public-ip" in lower,
        "P02-NEG-005": "no-ssh" in lower and not re.search(r"from_port\s*=\s*22", lower),
        "P02-NEG-006": "readonlyrootfilesystem" in lower
        and 'user                   = "10001"' in lower,
        "P02-NEG-007": "denyprivilegeescalation" in lower and "cross-account" in lower,
        "P02-NEG-008": "githubactionsrestrictedtrust" in lower
        and re.search(r"sts[.]amazonaws[.]com", lower) is not None,
        "P02-NEG-009": "privatelink" in lower and "public-access" in lower,
        "P02-NEG-010": "origin-authentication" in lower and "x-lengeas-edge" in lower,
        "P02-NEG-011": "cloudflare_source_ranges" in lower
        and "proxied = true" in lower
        and len(backend_keys) == 4,
        "P02-NEG-012": all(len(values) == 1 for values in backend_keys)
        and len({values[0] for values in backend_keys}) == 4,
        "P02-NEG-013": "lengeas/${var.environment}/" in lower
        and "secret values never enter terraform state" in lower,
    }


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
    source_files = files + sorted(TERRAFORM.rglob("*.js"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
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
        try:
            inventory = json.loads(CONTROL_INVENTORY.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return fail(f"negative-control inventory could not be read: {error}")
        controls = inventory.get("controls")
        if not isinstance(controls, list):
            return fail("negative-control inventory must contain a controls list")
        results = negative_control_checks(text)
        expected_ids = [item.get("id") for item in controls if isinstance(item, dict)]
        if set(expected_ids) != set(results):
            return fail("negative-control inventory and executable checks are out of sync")
        for item in controls:
            control_id = item["id"]
            if not results[control_id]:
                return fail(
                    f"negative control failed closed: {control_id} ({item.get('name', 'unnamed')})"
                )
        if re.search(r"(?im)^\s*(?:password|secret|token|api_key)\s*=", text):
            return fail("Terraform contains a secret-like assignment")
        print(f"PASS phase02-policy: {len(results)} inventory controls and secret policy present")
        return 0
    print(
        f"PASS phase02-policy: {len(MODULES)} modules and "
        f"{len(ROOTS)} environment roots compose safely"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
