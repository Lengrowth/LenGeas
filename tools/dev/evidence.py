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
    status = existing.get("status", "blocked")
    if status not in {"in_progress", "in_review", "blocked"}:
        status = "blocked"
    artifacts = []
    for value in PHASE02_ARTIFACT_PATHS:
        path = ROOT / value
        if not path.exists():
            raise SystemExit(f"Phase 02 evidence artifact is missing: {value}")
        artifacts.append({"path": value, "sha256": digest(path)})
    blockers = existing.get("blockers")
    if not isinstance(blockers, list):
        blockers = [
            "P02-T01 is blocked: the AWS account is not in an Organization and the "
            "authenticated profile cannot list or configure Organizations, CloudTrail, "
            "GuardDuty, Security Hub, or Control Tower.",
            "P02-T06 is blocked: Cloudflare deployment authentication and plan "
            "capability inventory are unavailable.",
            "P02-T07 is blocked: Supabase and Resend provider access is unavailable.",
            "P02-T09 is blocked: no approved recurring-cost ceiling or authorized "
            "exercise environment apply has been recorded.",
        ]
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
        # A blocked phase may have design artifacts and reviewable contracts, but
        # task completion is reserved for task records explicitly marked accepted.
        "completed_task_ids": [],
        "requirement_ids": ["RQ-019", "RQ-020", "RQ-021"],
        "artifacts": artifacts,
        "tests": [
            "Phase 01 accepted gate: uv run --frozen python tools/dev/task_runner.py phase-gate 01",
            "Phase 02 static module/root contract policy",
            "Phase 02 mandatory negative-control policy",
            "Terraform fmt and provider-backed validation of the changed modules; "
            "full-root validation is CI-only and no apply was run",
            "redacted AWS/GitHub inventory: read-only and limited",
            "live Phase 02 apply, failover, reachability, Cloudflare, Supabase, "
            "Resend, and reproduction scenarios: not run",
        ],
        "open_risks": [
            "All Phase 02 persistent resources remain planned-only until "
            "account/provider access and explicit cost approval are recorded.",
            "Cloudflare plan capabilities, managed WAF/bot/Turnstile/Access "
            "entitlements, and origin-auth rotation are unverified.",
            "Production recurring monthly estimate is not final until approved "
            "account, service sizing, and vendor plan data are supplied.",
        ],
        "next_phase_prerequisites": []
        if status == "in_review"
        else [
            "Resolve all mandatory blockers and rerun live evidence",
            "Independent review and explicit repository-owner acceptance",
        ],
        "blockers": blockers,
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
    if args.phase != "01":
        raise SystemExit("supported evidence phases are 01 and 02")
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
