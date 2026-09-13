"""Generated from packages/schemas/evidence/phase-manifest.schema.json."""

from typing import Literal, TypedDict

PhaseStatus = Literal['in_progress', 'in_review', 'accepted', 'blocked']

class Artifact(TypedDict, total=False):
    path: str
    sha256: str
    hash_scope: str

class PhaseManifest(TypedDict):
    schema_version: str
    phase: str
    status: PhaseStatus
    start_utc: str
    end_utc: str
    base_commit: str
    final_commit: str
    agent_identity: str
    toolchain: dict[str, str]
    completed_task_ids: list[str]
    requirement_ids: list[str]
    artifacts: list[Artifact]
    tests: list[str]
    open_risks: list[str]
    next_phase_prerequisites: list[str]
