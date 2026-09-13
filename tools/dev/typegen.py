"""Small, deterministic type-generation foundation for the evidence contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def generate_types() -> None:
    python_out = ROOT / "packages" / "shared-types" / "generated" / "phase_manifest.py"
    python_out.parent.mkdir(parents=True, exist_ok=True)
    python_out.write_text(
        '"""Generated from packages/schemas/evidence/phase-manifest.schema.json."""\n\n'
        "from typing import Literal, TypedDict\n\n"
        "PhaseStatus = Literal['in_progress', 'in_review', 'accepted', 'blocked']\n\n"
        "class Artifact(TypedDict, total=False):\n"
        "    path: str\n    sha256: str\n    hash_scope: str\n\n"
        "class PhaseManifest(TypedDict):\n"
        "    schema_version: str\n    phase: str\n    status: PhaseStatus\n"
        "    start_utc: str\n    end_utc: str\n    base_commit: str\n    final_commit: str\n"
        "    agent_identity: str\n    toolchain: dict[str, str]\n    completed_task_ids: list[str]\n"
        "    requirement_ids: list[str]\n    artifacts: list[Artifact]\n    tests: list[str]\n"
        "    open_risks: list[str]\n    next_phase_prerequisites: list[str]\n",
        encoding="utf-8",
    )
    typescript_out = ROOT / "packages" / "shared-types" / "generated" / "phase-manifest.ts"
    typescript_out.write_text(
        "// Generated from packages/schemas/evidence/phase-manifest.schema.json.\n"
        "export type PhaseStatus = 'in_progress' | 'in_review' | 'accepted' | 'blocked';\n"
        "export type Artifact = { path: string; sha256: string; hash_scope?: string };\n"
        "export type PhaseManifest = { schema_version: string; phase: string; status: PhaseStatus; "
        "start_utc: string; end_utc: string; base_commit: string; final_commit: string; agent_identity: string; "
        "toolchain: Record<string, string>; completed_task_ids: string[]; requirement_ids: string[]; "
        "artifacts: Artifact[]; tests: string[]; open_risks: string[]; next_phase_prerequisites: string[] };\n",
        encoding="utf-8",
    )

