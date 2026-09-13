// Generated from packages/schemas/evidence/phase-manifest.schema.json.
export type PhaseStatus = 'in_progress' | 'in_review' | 'accepted' | 'blocked';
export type Artifact = { path: string; sha256: string; hash_scope?: string };
export type PhaseManifest = { schema_version: string; phase: string; status: PhaseStatus; start_utc: string; end_utc: string; base_commit: string; final_commit: string; agent_identity: string; toolchain: Record<string, string>; completed_task_ids: string[]; requirement_ids: string[]; artifacts: Artifact[]; tests: string[]; open_risks: string[]; next_phase_prerequisites: string[] };
