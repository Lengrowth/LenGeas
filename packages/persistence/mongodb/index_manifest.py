"""Canonical Phase 03 collection/index manifest."""

COLLECTION_INDEXES: dict[str, tuple[str, ...]] = {
    "player_identities": ("uq_provider_subject", "uq_guest_device_key"),
    "studio_memberships": ("uq_studio_membership",),
    "service_accounts": ("uq_service_client_id",),
    "merge_idempotency": ("uq_merge_idempotency_scope",),
    "audit_logs": ("audit_studio_time", "audit_subject_time"),
}
