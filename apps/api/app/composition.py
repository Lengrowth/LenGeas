"""Explicit production composition for the API and durable Mongo boundaries."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from pymongo import AsyncMongoClient, MongoClient

from packages.persistence.mongodb.coordination import MongoCoordinationStore
from packages.persistence.mongodb.domain_repository import (
    MongoIdentityDomainRepository,
    MongoTenantDomainRepository,
)

from .auth.jwt import SupabaseJwtVerifier
from .auth.provider import SupabaseProviderIdentityVerifier
from .auth.turnstile import HttpTurnstileVerifier
from .main import create_app


def create_production_app() -> FastAPI:
    required = {
        "MONGODB_URI": os.environ.get("MONGODB_URI", "").strip(),
        "SUPABASE_JWKS_URL": os.environ.get("SUPABASE_JWKS_URL", "").strip(),
        "SUPABASE_ISSUER": os.environ.get("SUPABASE_ISSUER", "").strip(),
        "SUPABASE_AUDIENCE": os.environ.get("SUPABASE_AUDIENCE", "").strip(),
        "TURNSTILE_SECRET": os.environ.get("TURNSTILE_SECRET", "").strip(),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        if len(missing) != len(required):
            raise RuntimeError("production_configuration_incomplete:" + ",".join(missing))
        return create_app(allow_unconfigured=True)
    database_name = os.environ.get("MONGODB_DATABASE", "lengeas")
    sync_client: Any = MongoClient(required["MONGODB_URI"], tz_aware=True)
    async_client: Any = AsyncMongoClient(required["MONGODB_URI"], tz_aware=True)
    database = sync_client[database_name]
    async_database = async_client[database_name]
    coordination = MongoCoordinationStore(async_database)
    database.accounts.create_index("account_id", unique=True)
    database.player_identities.create_index(
        [("provider", 1), ("subject_or_credential_hash", 1)],
        unique=True,
        name="uq_provider_subject",
    )
    database.player_identities.create_index(
        "device_key_fingerprint", unique=True, sparse=True, name="uq_guest_device_key"
    )
    database.game_profiles.create_index(
        [("studio_id", 1), ("game_id", 1), ("player_id", 1)],
        unique=True,
        name="uq_game_profile",
    )
    database.studio_memberships.create_index(
        [("studio_id", 1), ("account_id", 1)], unique=True, name="uq_studio_membership"
    )
    database.service_accounts.create_index("client_id", unique=True, name="uq_service_client_id")
    database.merge_idempotency.create_index(
        [("studio_id", 1), ("actor_id", 1), ("idempotency_key", 1)],
        unique=True,
        name="uq_merge_idempotency_scope",
    )
    database.merge_previews.create_index("preview_id", unique=True, name="uq_merge_preview_id")
    database.merge_previews.create_index(
        "expires_at", expireAfterSeconds=0, name="merge_preview_expiry"
    )
    database.guest_credentials.create_index(
        "identity_id", unique=True, name="uq_guest_credential_identity"
    )
    database.guest_device_counts.create_index(
        "device_hash", unique=True, name="uq_guest_device_hash"
    )
    database.privacy_requests.create_index("request_id", unique=True, name="uq_privacy_request")
    database.privacy_requests.create_index(
        [("account_id", 1), ("status", 1)], name="privacy_account_status"
    )
    database.privacy_holds.create_index("account_id", unique=True, name="uq_privacy_hold_account")
    database.financial_history.create_index(
        [("studio_id", 1), ("account_id", 1)],
        unique=True,
        name="uq_financial_history_scope",
    )
    database.audit_events.create_index(
        [("studio_id", 1), ("occurred_at", -1)], name="audit_studio_time"
    )
    database.audit_events.create_index(
        [("subject_id", 1), ("occurred_at", -1)], name="audit_subject_time"
    )
    database.event_outbox.create_index("event_id", unique=True, name="uq_event_id")
    identity = MongoIdentityDomainRepository(database)
    tenancy = MongoTenantDomainRepository(database)
    verifier = SupabaseJwtVerifier(
        required["SUPABASE_JWKS_URL"],
        required["SUPABASE_ISSUER"],
        required["SUPABASE_AUDIENCE"],
        revocation_store=coordination,
    )
    turnstile = HttpTurnstileVerifier(required["TURNSTILE_SECRET"])
    app = create_app(
        identity=identity,
        tenancy=tenancy,
        jwt_verifier=verifier,
        turnstile=turnstile,
        provider_verifier=SupabaseProviderIdentityVerifier(verifier),
        revocation_store=coordination,
        proof_store=coordination,
        idempotency_store=coordination,
    )
    app.router.add_event_handler("startup", coordination.ensure_indexes)
    app.state.mongo_client = sync_client
    app.state.mongo_async_client = async_client
    return app
