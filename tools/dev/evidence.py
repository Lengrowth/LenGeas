"""Create and validate the Phase evidence manifest without hidden state."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.is_file():
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    else:
        excluded = {".git", ".venv", "node_modules", "__pycache__"}
        for child in sorted(
            item
            for item in path.rglob("*")
            if item.is_file() and not excluded.intersection(item.parts)
        ):
            hasher.update(child.relative_to(path).as_posix().encode("utf-8"))
            hasher.update(bytes.fromhex(digest(child)))
    return hasher.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase")
    args = parser.parse_args()
    if args.phase != "01":
        raise SystemExit("only Phase 01 evidence is implemented")
    evidence = ROOT / "docs" / "evidence" / "phase-01"
    manifest_path = evidence / "manifest.json"
    artifact_paths = [
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
    ]
    artifacts = []
    for value in artifact_paths:
        path = ROOT / value
        if path.exists():
            artifacts.append({"path": value, "sha256": digest(path)})
    task_ids = ["P01-T01", "P01-T02", "P01-T03", "P01-T04", "P01-T06", "P01-T07"]
    manifest = {
        "schema_version": "1.0.0",
        "phase": "01",
        "status": "blocked",
        "start_utc": "2026-09-13T09:02:42Z",
        "end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "base_commit": "28bd5d577c7f990854b364b4aa89a41fb144b4fa",
        "final_commit": git_head(),
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
            "server-side Compose smoke (passed; Docker was not run locally)",
            "server-side integration and server-local/public E2E harnesses (passed)",
            "task verify (still blocked by remote policy and signing prerequisites)",
            "task phase:gate PHASE=01 (blocked by BLK-03 and BLK-04)",
            "GitHub verify workflow dispatch (startup_failure; no jobs)",
        ],
        "open_risks": [
            "Docker runtime intentionally unavailable on the developer workstation; server runtime passed",
            "GitHub remote and live branch policy unavailable",
            "Sigstore signing unavailable",
        ],
        "next_phase_prerequisites": [
            "Independent review and resolution of all blockers",
            "Phase 01 acceptance",
        ],
        "blockers": ["BLK-03", "BLK-04"],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

    schema = json.loads(
        (ROOT / "packages" / "schemas" / "evidence" / "phase-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=str,
    )
    if errors:
        raise SystemExit(
            "evidence manifest schema validation failed: "
            + "; ".join(error.message for error in errors)
        )
    for artifact in artifacts:
        if artifact["sha256"] != digest(ROOT / str(artifact["path"])):
            raise SystemExit(f"evidence artifact digest changed: {artifact['path']}")
    print(f"PASS evidence manifest generated: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
