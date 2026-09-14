"""Repository-only CI policy checks for the Phase 01 verification workflow."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
EXPECTED_WORKFLOWS = {"verify.yml", "release.yml", "dependency-review.yml", "codeql.yml"}
ACTION_REF = re.compile(r"uses:\s*[^\s#]+@(?P<ref>v?\d+\.\d+\.\d+(?:\.\d+)?)\s*(?:#.*)?$")
LOCAL_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def fail(message: str) -> int:
    print(f"FAIL {message}", file=sys.stderr)
    return 1


def workflow_policy() -> int:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return fail("PyYAML is required for workflow policy validation")

    files = {path.name for path in WORKFLOW_DIR.glob("*.yml")}
    if files != EXPECTED_WORKFLOWS:
        return fail(f"workflow set is {sorted(files)!r}; expected {sorted(EXPECTED_WORKFLOWS)!r}")

    mandatory_tokens = (
        "format",
        "lint",
        "typecheck",
        "unit",
        "property",
        "contract",
        "integration",
        "e2e",
        "security",
        "performance",
        "determinism",
        "disaster-recovery",
        "schema",
        "openapi",
        "terraform",
        "gitleaks",
        "trivy",
        "sbom",
        "docs-links",
    )
    verify_text = (WORKFLOW_DIR / "verify.yml").read_text(encoding="utf-8")
    missing = [token for token in mandatory_tokens if token not in verify_text]
    if missing:
        return fail(f"verify workflow is missing mandatory gates: {', '.join(missing)}")

    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            return fail(f"{path.relative_to(ROOT)} is invalid YAML: {error}")
        if not isinstance(document, dict):
            return fail(f"{path.relative_to(ROOT)} must contain a YAML mapping")
        if "permissions:" not in text:
            return fail(f"{path.relative_to(ROOT)} must declare least-privilege permissions")
        if "write-all" in text or "continue-on-error" in text:
            return fail(
                f"{path.relative_to(ROOT)} contains an unsafe permission or failure override"
            )
        if re.search(r"(?im)^\s*if:\s*(?:\$\{\{\s*)?(?:false|0)(?:\s*\}\})?\s*$", text):
            return fail(f"{path.relative_to(ROOT)} contains a disabled step or job")
        if re.search(r"(?m)\|\|\s*(?:true|exit\s+0)\b", text):
            return fail(f"{path.relative_to(ROOT)} masks a mandatory command failure")
        for line in text.splitlines():
            if "uses:" in line and not ACTION_REF.search(line):
                return fail(
                    f"{path.relative_to(ROOT)} has an action without an exact version: "
                    f"{line.strip()}"
                )
    print(f"PASS workflow-policy: {len(files)} workflows, exact action refs, and fail-closed gates")
    return 0


def terraform_policy() -> int:
    files = sorted((ROOT / "infrastructure" / "terraform").rglob("*.tf"))
    if not files:
        return fail("no Terraform configuration found")
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    if not re.search(r'required_version\s*=\s*"=\s*1\.15\.8"', text):
        return fail("Terraform must pin required_version to 1.15.8")
    expected = {
        "aws": ("hashicorp/aws", "6.62.0"),
        "cloudflare": ("cloudflare/cloudflare", "5.24.0"),
        "mongodbatlas": ("mongodb/mongodbatlas", "2.17.0"),
        "supabase": ("supabase/supabase", "1.10.1"),
    }
    for name, (source, version) in expected.items():
        block = re.search(rf"{name}\s*=\s*\{{(?P<body>.*?)\n\s*\}}", text, re.DOTALL)
        if block is None:
            return fail(f"Terraform provider {name!r} is not declared")
        body = block.group("body")
        if f'source  = "{source}"' not in body and f'source = "{source}"' not in body:
            return fail(f"Terraform provider {name!r} has unexpected source")
        if f'version = "= {version}"' not in body:
            return fail(f"Terraform provider {name!r} must be pinned to {version}")
    if 'backend "s3"' not in text or "use_lockfile = true" not in text:
        return fail("ADR-0010 S3 backend must enable native use_lockfile")
    phase02 = ROOT / "docs" / "evidence" / "phase-02"
    if phase02.exists():
        checker = ROOT / "tools" / "dev" / "phase02_checks.py"
        completed = subprocess.run(
            [sys.executable, str(checker), "contract"], cwd=ROOT, check=False
        )
        if completed.returncode:
            return fail("Phase 02 Terraform contract checks failed")
    elif re.search(r"(?im)^\s*(resource|module|data)\s+\"", text):
        return fail("Phase 01 Terraform policy must not provision live resources")
    if re.search(r"(?i)(access_key|secret_key|api[_-]?key|password|token)\s*=", text):
        return fail("Terraform configuration must not contain credentials")
    print(
        f"PASS terraform-policy: {len(files)} HCL files, exact provider pins, "
        + (
            "Phase 02 contract and no credentials"
            if phase02.exists()
            else "no resources or credentials"
        )
    )
    return 0


def docs_links() -> int:
    missing: list[str] = []
    for document in sorted(ROOT.rglob("*.md")):
        if (
            ".git" in document.parts
            or "node_modules" in document.parts
            or ".venv" in document.parts
            or ".terraform" in document.parts
        ):
            continue
        for match in LOCAL_LINK.finditer(document.read_text(encoding="utf-8")):
            target = match.group(1).strip().split("#", 1)[0].strip().strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "//")):
                continue
            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                missing.append(f"{document.relative_to(ROOT)} -> {target} (outside repository)")
                continue
            if not resolved.exists():
                missing.append(f"{document.relative_to(ROOT)} -> {target}")
    if missing:
        return fail("broken local documentation links:\n" + "\n".join(missing))
    print("PASS docs-links: all repository-relative Markdown links resolve")
    return 0


def schema_check() -> int:
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
    except ImportError:
        return fail("jsonschema is required for schema validation")
    schema_path = ROOT / "packages" / "schemas" / "evidence" / "phase-manifest.schema.json"
    try:
        schema: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        vectors = sorted(
            (ROOT / "packages" / "schemas" / "canonical" / "vectors").glob("fixture_*.json")
        )
        if not vectors:
            return fail("canonical schema vectors are required")
        for vector in vectors:
            value = json.loads(vector.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or "canonical_utf8" not in value:
                return fail(f"{vector.relative_to(ROOT)} is not a canonical vector")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return fail(f"schema validation failed: {error}")
    print("PASS schema: Draft 2020-12 evidence schema and canonical vectors validate")
    return 0


def openapi_check() -> int:
    candidates = sorted(
        path
        for root in (ROOT / "apps", ROOT / "packages", ROOT / "docs")
        for path in root.rglob("*")
        if path.is_file()
        and path.name.lower().startswith("openapi")
        and path.suffix.lower() == ".json"
    )
    if candidates:
        for path in candidates:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                return fail(f"{path.relative_to(ROOT)} is not valid JSON: {error}")
            if not isinstance(document, dict) or not str(document.get("openapi", "")).startswith(
                "3.1"
            ):
                return fail(f"{path.relative_to(ROOT)} must be an OpenAPI 3.1 document")
        print(f"PASS openapi: {len(candidates)} OpenAPI 3.1 document(s) validate")
        return 0

    tool_path = ROOT / "tools" / "dev" / "openapi_diff.py"
    spec = importlib.util.spec_from_file_location("lengeas_openapi_diff", tool_path)
    if spec is None or spec.loader is None:
        return fail("OpenAPI compatibility tool is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as directory:
        baseline = Path(directory) / "baseline.json"
        candidate = Path(directory) / "candidate.json"
        document = {
            "openapi": "3.1.0",
            "info": {"title": "fixture", "version": "0.1.0"},
            "paths": {},
        }
        baseline.write_text(json.dumps(document), encoding="utf-8")
        candidate.write_text(json.dumps(document), encoding="utf-8")
        if module.compare(baseline, candidate):
            return fail("OpenAPI compatibility tool rejected identical documents")
        candidate.write_text(
            json.dumps({**document, "info": {"title": "changed", "version": "0.1.0"}}),
            encoding="utf-8",
        )
        if not module.compare(baseline, candidate):
            return fail("OpenAPI compatibility tool accepted a changed document")
    print(
        "PASS openapi: compatibility gate rejects changes and accepts identical "
        "OpenAPI 3.1 fixtures"
    )
    return 0


def license_policy() -> int:
    files = [
        ROOT / "package.json",
        ROOT / "pnpm-lock.yaml",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    forbidden = ("GPL-3.0", "AGPL-3.0", "GPLv3", "AGPLv3")
    findings = [
        f"{path.relative_to(ROOT)} contains {license}"
        for path in files
        if path.exists()
        for license in forbidden
        if license in path.read_text(encoding="utf-8")
    ]
    if findings:
        return fail("forbidden dependency licenses detected:\n" + "\n".join(findings))
    print(
        "PASS license-policy: dependency manifests contain no denied GPL/AGPL license identifiers"
    )
    return 0


def phase02_policy() -> int:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dev" / "phase02_checks.py"), "contract"],
        cwd=ROOT,
        check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "check",
        choices=(
            "workflow-policy",
            "terraform-policy",
            "docs-links",
            "schema",
            "openapi",
            "license-policy",
            "phase02-policy",
        ),
    )
    check = parser.parse_args().check
    return {
        "workflow-policy": workflow_policy,
        "terraform-policy": terraform_policy,
        "docs-links": docs_links,
        "schema": schema_check,
        "openapi": openapi_check,
        "license-policy": license_policy,
        "phase02-policy": phase02_policy,
    }[check]()


if __name__ == "__main__":
    raise SystemExit(main())
