"""Canonical Phase 03 collection/index manifest."""

COLLECTION_INDEXES: dict[str, tuple[str, ...]] = {
    "player_identities": ("uq_provider_subject", "uq_guest_device_key"),
    "studio_memberships": ("uq_studio_membership",),
    "service_accounts": ("uq_service_client_id",),
    "merge_idempotency": ("uq_merge_idempotency_scope",),
    "merge_previews": ("uq_merge_preview_id", "merge_preview_expiry"),
    "guest_credentials": ("uq_guest_credential_identity",),
    "guest_device_counts": ("uq_guest_device_hash",),
    "privacy_requests": ("uq_privacy_request", "privacy_account_status"),
    "privacy_holds": ("uq_privacy_hold_account",),
    "financial_history": ("uq_financial_history_scope",),
    "audit_events": ("audit_studio_time", "audit_subject_time"),
    "event_outbox": ("uq_event_id",),
    "proof_consumptions": ("uq_consumed_proof", "proof_consumption_expiry"),
}
