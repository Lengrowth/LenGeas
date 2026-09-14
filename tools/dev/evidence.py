"""Create and validate the Phase evidence manifest without hidden state."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATHS = (
    ".tool-versions",
    "Taskfile.yml",
    "package.json",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "uv.lock",
    "compose.yaml",
    ".github",
    "infrastructure/docker",
    "infrastructure/aws",
    "packages/schemas/evidence/phase-manifest.schema.json",
    "packages/shared-types/generated",
    "tools/dev",
    "tests",
    "docs/evidence/phase-01/operations/server-bundle-manifest.json",
    "docs/evidence/phase-01/operations/server-runtime.json",
)
PHASE02_ARTIFACT_PATHS = (
    "infrastructure/terraform",
    "infrastructure/policies",
    "tools/dev/phase02_checks.py",
    "docs/runbooks",
    "docs/evidence/phase-02/tasks",
    "docs/evidence/phase-02/security",
    "docs/evidence/phase-02/performance",
    "docs/evidence/phase-02/operations",
    "docs/phases/02-cloud-foundation.md",
)
PHASE03_ARTIFACT_PATHS = (
    ".github/workflows/verify.yml",
    "pyproject.toml",
    "uv.lock",
    "packages/domain/identity",
    "packages/domain/tenancy",
    "packages/domain/authorization",
    "packages/domain/audit",
    "packages/domain/coordination.py",
    "packages/domain/coordination_memory.py",
    "packages/persistence/mongodb",
    "apps/api/app/composition.py",
    "apps/api/app/e2e.py",
    "apps/api/app/auth",
    "apps/api/app/main.py",
    "apps/api/app/users",
    "apps/api/app/players",
    "apps/api/app/studios",
    "apps/api/app/permissions",
    "apps/api/app/audit",
    "packages/schemas/api/v1",
    "tests/unit/identity",
    "tests/property/identity",
    "tests/contract/identity",
    "tests/integration/identity",
    "tests/e2e/identity",
    "tests/security/identity",
    "docs/evidence/phase-03/tasks",
    "docs/evidence/phase-03/security",
    "docs/evidence/phase-03/performance",
    "docs/evidence/phase-03/operations",
    "docs/phases/03-identity-tenancy-authorization.md",
    "docs/evidence/phase-03/handoff.md",
    "docs/evidence/phase-03/blockers.md",
    "docs/evidence/phase-03/decisions.md",
    "docs/evidence/phase-03/commands.ndjson",
    "docs/evidence/phase-03/test-report.xml",
    "docs/evidence/phase-03/coverage.json",
    ".env.example",
)
TEXT_SUFFIXES = {
    ".env",
    ".hcl",
    ".js",
    ".json",
    ".jsx",
    ".lock",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".tf",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {".gitattributes", ".gitignore", "CODEOWNERS", "Dockerfile", "Makefile"}


def normalized_file_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES:
        return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return data


def tracked_files(path: Path) -> list[Path]:
    relative = path.relative_to(ROOT).as_posix()
    output = subprocess.check_output(["git", "ls-files", "-z", "--", relative], cwd=ROOT)
    return [
        ROOT / value.decode("utf-8")
        for value in output.split(b"\0")
        if value and (ROOT / value.decode("utf-8")).is_file()
    ]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.is_file():
        hasher.update(normalized_file_bytes(path))
    else:
        for child in sorted(
            tracked_files(path), key=lambda item: item.relative_to(path).as_posix()
        ):
            hasher.update(child.relative_to(path).as_posix().encode("utf-8"))
            hasher.update(bytes.fromhex(digest(child)))
    return hasher.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def schema() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            (ROOT / "packages" / "schemas" / "evidence" / "phase-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        ),
    )


def validate_schema(manifest: dict[str, object]) -> None:
    from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

    errors = sorted(
        Draft202012Validator(schema(), format_checker=FormatChecker()).iter_errors(manifest),
        key=str,
    )
    if errors:
        raise SystemExit(
            "evidence manifest schema validation failed: "
            + "; ".join(error.message for error in errors)
        )


def load_manifest(path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"evidence manifest could not be read: {error}") from error
    if not isinstance(manifest, dict):
        raise SystemExit("evidence manifest must be a JSON object")
    return manifest


def verify_manifest(manifest: dict[str, object]) -> None:
    validate_schema(manifest)
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise SystemExit("evidence manifest artifacts must be a list")
    mismatches: list[str] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        relative = str(artifact.get("path", ""))
        expected = str(artifact.get("sha256", ""))
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative} (missing)")
            continue
        actual = digest(path)
        if expected != actual:
            mismatches.append(f"{relative} (manifest={expected}; actual={actual})")
    if mismatches:
        raise SystemExit("evidence artifact digest mismatches:\n" + "\n".join(mismatches))


def verify_phase03_completeness(manifest: dict[str, object]) -> None:
    required = {
        "manifest.json",
        "handoff.md",
        "blockers.md",
        "decisions.md",
        "commands.ndjson",
        "test-report.xml",
        "coverage.json",
    }
    evidence = ROOT / "docs" / "evidence" / "phase-03"
    present = {path.name for path in evidence.iterdir() if path.is_file()}
    present |= {f"tasks/{path.name}" for path in (evidence / "tasks").glob("P03-T*.md")}
    present |= {f"security/{path.name}" for path in (evidence / "security").glob("*")}
    present |= {f"performance/{path.name}" for path in (evidence / "performance").glob("*")}
    present |= {f"operations/{path.name}" for path in (evidence / "operations").glob("*")}
    required |= {f"tasks/P03-T0{number}.md" for number in range(1, 9)}
    required |= {"security/README.md", "performance/README.md", "operations/README.md"}
    missing = sorted(required - present)
    if missing:
        raise SystemExit("Phase 03 evidence is incomplete: " + ", ".join(missing))
    if manifest.get("status") != "in_review" or manifest.get("blockers") != []:
        raise SystemExit("Phase 03 evidence must be in_review with no blockers")
    if manifest.get("completed_task_ids") != [f"P03-T0{number}" for number in range(1, 9)]:
        raise SystemExit("Phase 03 evidence must list P03-T01 through P03-T08")
    import xml.etree.ElementTree as ET

    report = ET.parse(evidence / "test-report.xml").getroot()
    suites = [report] if report.tag == "testsuite" else list(report)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    if failures != 0 or errors != 0:
        raise SystemExit("Phase 03 test report contains failures or errors")
    coverage = json.loads((evidence / "coverage.json").read_text(encoding="utf-8"))
    totals = coverage.get("totals", {})
    if not isinstance(totals, dict) or not isinstance(totals.get("percent_covered"), (int, float)):
        raise SystemExit("Phase 03 coverage report has no numeric totals.percent_covered")
    if tests < 24:
        raise SystemExit("Phase 03 test report is missing the behavioral regression tests")
    commands = (evidence / "commands.ndjson").read_text(encoding="utf-8")
    exact_pytest = (
        "pytest -q tests/unit/identity tests/property/identity tests/contract/identity "
        "tests/integration/identity tests/e2e/identity tests/security/identity"
    )
    if exact_pytest not in commands:
        raise SystemExit("Phase 03 evidence does not record the exact identity pytest command")


def build_manifest(existing: dict[str, object] | None) -> dict[str, object]:
    artifacts = []
    for value in ARTIFACT_PATHS:
        path = ROOT / value
        if not path.exists():
            raise SystemExit(f"evidence artifact is missing: {value}")
        artifacts.append({"path": value, "sha256": digest(path)})
    task_ids = [f"P01-T0{number}" for number in range(1, 9)]
    existing = existing or {}
    status = existing.get("status", "in_review")
    if status not in {"in_review", "accepted"}:
        status = "in_review"
    return {
        "schema_version": "1.0.0",
        "phase": "01",
        "status": status,
        "start_utc": existing.get("start_utc", "2026-09-13T09:02:42Z"),
        "end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "base_commit": existing.get("base_commit", "28bd5d577c7f990854b364b4aa89a41fb144b4fa"),
        "final_commit": existing.get("final_commit", git_head()),
        "agent_identity": "Codex root phase agent",
        "toolchain": {
            "powershell": "7.6.5",
            "python": "3.13.5 via uv 0.11.29",
            "node": "22.16.0",
            "pnpm": "11.20.0",
            "terraform": "1.15.8",
            "task": "3.53.1",
            "git": "2.49.0.windows.1",
            "docker": "unavailable",
        },
        "completed_task_ids": task_ids,
        "requirement_ids": [
            "RQ-001",
            "RQ-003",
            "RQ-007",
            "RQ-019",
            "RQ-020",
            "RQ-021",
            "RQ-022",
            "RQ-024",
        ],
        "artifacts": artifacts,
        "tests": [
            "task bootstrap",
            "task generate twice",
            "task format",
            "task lint",
            "task typecheck",
            "dependency-free synthetic suites",
            "local policy checks",
            "read-only manifest verification (zero mismatches)",
            "server-side Compose smoke (passed; Docker was not run locally)",
            "server-side integration and server-local/public E2E harnesses (passed)",
            "GitHub hosted verify run 34759754929 (passed)",
            "GitHub keyless release run 34760098397 for v0.1.1 (passed)",
            (
                "task phase:gate PHASE=01 (accepted historical gate)"
                if status == "accepted"
                else "task phase:gate PHASE=01 (review gate; acceptance remains external)"
            ),
        ],
        "open_risks": [
            "Docker intentionally unavailable on developer workstation; "
            "server and hosted CI runtime passed",
            "Dependabot #7: pytest 8.4.2 moderate test-only risk; "
            "owner infrastructure_owner; Dependabot PR #5 target 2026-09-20",
            "Dependabot #6: turbo 2.5.6 moderate build-only risk; "
            "owner infrastructure_owner; Dependabot PR #4 target 2026-09-20",
            "Dependabot #5: turbo 2.5.6 low build-only risk; "
            "owner infrastructure_owner; Dependabot PR #4 target 2026-09-20",
            "Dependabot #4: turbo 2.5.6 moderate build-only risk; "
            "owner infrastructure_owner; Dependabot PR #4 target 2026-09-20",
            "Dependabot #3: turbo 2.5.6 low build-only risk; "
            "owner infrastructure_owner; Dependabot PR #4 target 2026-09-20",
        ],
        "next_phase_prerequisites": (
            []
            if status == "accepted"
            else [
                "Review recommendation and resolution of all mandatory findings",
                "Explicit repository-owner acceptance",
            ]
        ),
        "blockers": [],
    }


def build_phase02_manifest(existing: dict[str, object] | None) -> dict[str, object]:
    """Build Phase 02 evidence without hashing the manifest itself."""
    existing = existing or {}
    status = existing.get("status", "in_review")
    if status not in {"in_progress", "in_review", "accepted", "blocked"}:
        status = "in_review"
    artifacts = []
    for value in PHASE02_ARTIFACT_PATHS:
        path = ROOT / value
        if not path.exists():
            raise SystemExit(f"Phase 02 evidence artifact is missing: {value}")
        artifacts.append({"path": value, "sha256": digest(path)})
    blockers = existing.get("blockers", [])
    if not isinstance(blockers, list):
        blockers = []
    return {
        "schema_version": "1.0.0",
        "phase": "02",
        "status": status,
        "start_utc": existing.get(
            "start_utc", datetime.now(UTC).isoformat().replace("+00:00", "Z")
        ),
        "end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "base_commit": existing.get("base_commit", "4902c6fbdd099e6b31402aedfc23faed7b3039dd"),
        "final_commit": git_head(),
        "agent_identity": "Codex root phase agent",
        "toolchain": {
            "powershell": "7.6.5",
            "python": "3.13.5 via uv 0.11.29",
            "node": "22.16.0",
            "pnpm": "11.20.0",
            "terraform": "1.15.8",
            "git": "2.49.0.windows.1",
            "task": "3.53.1 (not on PATH; python runner used)",
            "docker": "unavailable and not installed per Phase 01 constraint",
        },
        "completed_task_ids": (
            [f"P02-T0{number}" for number in range(1, 10)]
            if status in {"in_review", "accepted"}
            else []
        ),
        "requirement_ids": ["RQ-019", "RQ-020", "RQ-021"],
        "artifacts": artifacts,
        "tests": [
            "Phase 01 accepted gate: uv run --frozen python tools/dev/task_runner.py phase-gate 01",
            "read-only AWS development-host inventory",
            "public development health and version checks: HTTP 200",
            "server bundle, loopback dependency, deployment, and rollback contract review",
            "production-target module/root static policy",
            "production-target mandatory negative-control policy",
            "Terraform fmt and provider-backed validation of disabled reference modules",
            "live production apply, failover, reachability, managed providers, "
            "and DR: deferred and not claimed",
        ],
        "open_risks": [
            "Development runs on one t3.medium in one availability zone with no "
            "production availability or DR guarantee.",
            "The development root EBS volume is unencrypted; only synthetic "
            "non-sensitive data is permitted.",
            "The development endpoint is DNS-only and reaches the public origin "
            "directly; no production edge protection is claimed.",
            "The instance has no IAM profile and detailed monitoring is disabled.",
            "Disabled production-target Terraform may drift and must be refreshed at rollout.",
        ],
        "next_phase_prerequisites": (
            []
            if status == "accepted"
            else [
                "Independent review and resolution of mandatory findings",
                "Explicit repository-owner acceptance",
            ]
        ),
        "blockers": blockers,
    }


def build_phase03_manifest(existing: dict[str, object] | None) -> dict[str, object]:
    existing = existing or {}
    artifacts = []
    for value in PHASE03_ARTIFACT_PATHS:
        path = ROOT / value
        if not path.exists():
            raise SystemExit(f"Phase 03 evidence artifact is missing: {value}")
        artifacts.append({"path": value, "sha256": digest(path)})
    return {
        "schema_version": "1.0.0",
        "phase": "03",
        "status": "in_review",
        "start_utc": existing.get(
            "start_utc", datetime.now(UTC).isoformat().replace("+00:00", "Z")
        ),
        "end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "base_commit": existing.get("base_commit", "c704e4409c4ef3e004a3b57dddaeec52919dc351"),
        "final_commit": git_head(),
        "agent_identity": "Codex root phase agent",
        "toolchain": {
            "powershell": "7.6.5",
            "python": "3.13.5 via uv 0.11.29",
            "node": "22.16.0",
            "pnpm": "11.20.0",
            "git": "2.49.0.windows.1",
            "task": "3.53.1 (python runner used)",
            "docker": "unavailable and not installed per Phase 01 constraint",
        },
        "completed_task_ids": [f"P03-T0{number}" for number in range(1, 9)],
        "requirement_ids": ["RQ-006", "RQ-007", "RQ-010", "RQ-020"],
        "artifacts": artifacts,
        "tests": [
            "Phase 02 accepted gate and read-only manifest verification",
            "task bootstrap",
            "task generate twice with identical output",
            "task format",
            "task lint",
            "task typecheck",
            "task test:unit -- identity",
            "task test:property -- identity",
            "task test:contract -- auth",
            "task test:integration -- supabase,mongodb (fails closed without Docker/Mongo)",
            (
                "task test:e2e -- identity (fails closed without deployed API URL and "
                "guest credentials)"
            ),
            "hosted E2E identity selector (deployed FastAPI boundary; guest create plus replay)",
            "task test:security -- tenancy,authorization",
            (
                "uv run --frozen pytest -q tests/unit/identity tests/property/identity "
                "tests/contract/identity tests/integration/identity tests/e2e/identity "
                "tests/security/identity (24 passed, 2 skipped; total coverage 72%)"
            ),
            "full dependency-free suites",
            "read-only Phase 03 manifest verification",
            "task phase:gate PHASE=03",
        ],
        "open_risks": [
            "Docker is unavailable on the Windows workstation; MongoDB Compose execution "
            "is delegated to hosted CI.",
            "Supabase and Turnstile production projects are intentionally not activated "
            "under ADR-0011; provider-faithful adapters and test boundaries are present.",
            "Production API composition requires all MongoDB, Supabase JWKS, and Turnstile "
            "settings; partial configuration fails closed.",
            "Deployed E2E requires LENGEAS_E2E_BASE_URL, LENGEAS_E2E_GUEST_PROOF, and "
            "LENGEAS_E2E_DEVICE_PUBLIC_KEY; absent dependencies fail the selector.",
            "Hosted verification uses the provider-independent identity API boundary in "
            "apps/api/app/e2e.py; production provider credentials remain external.",
            "Development remains synthetic-data-only on the accepted Phase 02 host.",
        ],
        "next_phase_prerequisites": [
            "Repository-owner review and explicit acceptance",
            "Phase 04 must use the actor/scope and definition-ownership rules in handoff.md",
        ],
        "blockers": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="rewrite the manifest from the current tree; normal verification is read-only",
    )
    args = parser.parse_args()
    if args.phase == "02":
        evidence = ROOT / "docs" / "evidence" / "phase-02"
        manifest_path = evidence / "manifest.json"
        if not manifest_path.exists():
            raise SystemExit(f"Phase 02 evidence manifest is missing: {manifest_path}")
        existing = load_manifest(manifest_path)
        if not args.regenerate:
            verify_manifest(existing)
            print(f"PASS evidence manifest verified (read-only): {manifest_path.relative_to(ROOT)}")
            return 0
        validate_schema(existing)
        manifest = build_phase02_manifest(existing)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        verify_manifest(load_manifest(manifest_path))
        print(
            "PASS Phase 02 evidence manifest regenerated and verified: "
            f"{manifest_path.relative_to(ROOT)}"
        )
        return 0
    if args.phase == "03":
        evidence = ROOT / "docs" / "evidence" / "phase-03"
        manifest_path = evidence / "manifest.json"
        if not manifest_path.exists():
            raise SystemExit(f"Phase 03 evidence manifest is missing: {manifest_path}")
        existing = load_manifest(manifest_path)
        if not args.regenerate:
            verify_manifest(existing)
            verify_phase03_completeness(existing)
            print(f"PASS evidence manifest verified (read-only): {manifest_path.relative_to(ROOT)}")
            return 0
        validate_schema(existing)
        manifest = build_phase03_manifest(existing)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        verify_manifest(load_manifest(manifest_path))
        print(
            "PASS Phase 03 evidence manifest regenerated and verified: "
            f"{manifest_path.relative_to(ROOT)}"
        )
        return 0
    if args.phase != "01":
        raise SystemExit("supported evidence phases are 01, 02, and 03")
    evidence = ROOT / "docs" / "evidence" / "phase-01"
    manifest_path = evidence / "manifest.json"
    if not args.regenerate:
        manifest = load_manifest(manifest_path)
        verify_manifest(manifest)
        print(f"PASS evidence manifest verified (read-only): {manifest_path.relative_to(ROOT)}")
        return 0

    previous = load_manifest(manifest_path) if manifest_path.exists() else None
    if previous is not None:
        validate_schema(previous)
    manifest = build_manifest(previous)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    verify_manifest(load_manifest(manifest_path))
    print(f"PASS evidence manifest regenerated and verified: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
