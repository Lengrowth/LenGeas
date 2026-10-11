"""Phase-specific gate that fails closed when review prerequisites are open."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    phase = sys.argv[1] if len(sys.argv) > 1 else "01"
    path = ROOT / "docs" / "evidence" / f"phase-{phase}" / "manifest.json"
    if not path.exists():
        print(f"FAIL phase gate: missing {path}", file=sys.stderr)
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("phase") != phase:
        print(
            f"FAIL phase gate: manifest phase={manifest.get('phase')!r}; requested={phase!r}",
            file=sys.stderr,
        )
        return 1
    try:
        from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

        schema_path = ROOT / "packages" / "schemas" / "evidence" / "phase-manifest.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
            key=str,
        )
        if errors:
            print(f"FAIL phase gate: invalid manifest: {errors[0].message}", file=sys.stderr)
            return 1
    except (OSError, json.JSONDecodeError, ImportError) as error:
        print(f"FAIL phase gate: manifest schema unavailable: {error}", file=sys.stderr)
        return 1
    blockers = manifest.get("blockers", [])
    status = manifest.get("status")
    task_ids = manifest.get("completed_task_ids", [])
    if any(not str(task).startswith(f"P{phase}-") for task in task_ids):
        print("FAIL phase gate: manifest contains a task from another phase", file=sys.stderr)
        return 1
    if status not in {"in_review", "accepted"} or blockers:
        print(
            f"FAIL phase gate: status={manifest.get('status')!r}; blockers={blockers!r}",
            file=sys.stderr,
        )
        return 1
    if phase == "03":
        evidence_path = ROOT / "tools" / "dev" / "evidence.py"
        import importlib.util

        spec = importlib.util.spec_from_file_location("lengeas_evidence", evidence_path)
        if spec is None or spec.loader is None:
            print("FAIL phase gate: evidence validator unavailable", file=sys.stderr)
            return 1
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            module.verify_manifest(manifest)
            module.verify_phase03_completeness(manifest)
        except SystemExit as error:
            print(f"FAIL phase gate: {error}", file=sys.stderr)
            return 1
    print(f"PASS phase gate: Phase {phase} is {status} with no blockers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
