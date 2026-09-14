"""Versioned FastAPI composition root for Phase 03."""

from __future__ import annotations

from datetime import UTC

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response

from packages.domain.authorization.policy import (
    Actor,
    ActorKind,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.identity.merge import MergeService
from packages.domain.identity.privacy import PrivacyOperation, PrivacyService
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import Environment, MembershipRole, TrustedScope
from packages.domain.tenancy.repository import InMemoryTenantRepository
from packages.domain.tenancy.services import StudioAdministration
from packages.schemas.api.v1.auth.models import (
    CredentialRotateRequest,
    GuestCreateRequest,
    IdentityLinkRequest,
)
from packages.schemas.api.v1.players.models import (
    MergeCommitRequest,
    MergePreviewRequest,
    PrivacyRequestModel,
)
from packages.schemas.api.v1.studios.models import (
    InvitationRequest,
    MembershipRequest,
    RoleChangeRequest,
    ServiceAccountRequest,
    StudioCreateRequest,
)

from .auth.guest import GuestIdentityService
from .auth.turnstile import TurnstileVerifier


class AcceptingTurnstile:
    async def verify(self, proof: str, remote_ip: str | None) -> bool:
        return bool(proof)


def create_app(*, turnstile: TurnstileVerifier | None = None) -> FastAPI:
    app = FastAPI(
        title="LenGeas Identity and Tenancy API", version="1.0.0", openapi_version="3.1.0"
    )
    identity = InMemoryIdentityRepository()
    tenancy = InMemoryTenantRepository()
    merge = MergeService(identity)
    privacy = PrivacyService(identity)
    policies = PolicyDecisionService()
    admin = StudioAdministration(tenancy)
    app.state.admin = admin
    guest = GuestIdentityService(identity, turnstile or AcceptingTurnstile())
    app.state.identity = identity
    app.state.tenancy = tenancy
    app.state.guest = guest

    def scope(request: Request, *, game_id: str | None = None) -> TrustedScope:
        actor_id = request.headers.get("x-actor-id")
        studio_id = request.headers.get("x-studio-id")
        if not actor_id or not studio_id:
            raise HTTPException(status_code=401, detail={"code": "authentication_required"})
        return TrustedScope(
            actor_id,
            studio_id,
            game_id,
            Environment.TESTING,
            frozenset({MembershipRole.ADMIN}),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=409, content={"error": {"code": str(error), "message": str(error)}}
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"service": "platform-api", "status": "ok"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {"service": "platform-api", "version": "0.3.0", "status": "ok"}

    @app.post("/api/v1/auth/guests", status_code=status.HTTP_201_CREATED)
    async def create_guest(body: GuestCreateRequest, request: Request) -> dict[str, object]:
        credentials = await guest.create(
            body.turnstile_proof,
            body.device_public_key,
            request.client.host if request.client else None,
        )
        return {
            "player_id": credentials.player_id,
            "identity_id": credentials.identity_id,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expires_at.astimezone(UTC).isoformat(),
        }

    @app.post("/api/v1/auth/identity-links", status_code=status.HTTP_201_CREATED)
    async def link_identity(body: IdentityLinkRequest, request: Request) -> dict[str, str]:
        trusted = scope(request)
        player = identity.players.get(trusted.actor_id)
        if player is None:
            raise HTTPException(status_code=404, detail={"code": "player_not_found"})
        link = identity.link_identity(
            player.player_id,
            __import__(
                "packages.domain.identity.models", fromlist=["IdentityKind"]
            ).IdentityKind.SUPABASE,
            body.provider,
            body.subject,
        )
        return {"identity_id": link.identity_id, "player_id": link.player_id}

    @app.post("/api/v1/auth/credentials/rotate")
    async def rotate_credential(body: CredentialRotateRequest) -> dict[str, str]:
        return {"refresh_token": guest.rotate(body.identity_id, body.refresh_token)}

    @app.get("/api/v1/auth/current")
    async def current_account(request: Request) -> object:
        trusted = scope(request)
        account = identity.accounts.get(trusted.actor_id)
        if account is None or account.deleted_at is not None:
            raise HTTPException(status_code=404, detail={"code": "account_not_found"})
        return account

    @app.post("/api/v1/players/merge/preview")
    async def merge_preview(body: MergePreviewRequest, request: Request) -> object:
        return merge.preview(scope(request), body.source_player_id, body.target_player_id)

    @app.post("/api/v1/players/merge")
    async def merge_commit(body: MergeCommitRequest, request: Request) -> dict[str, str]:
        target = merge.commit(scope(request), body.preview_id, body.choices, body.idempotency_key)
        return {"player_id": target}

    @app.post("/api/v1/privacy/requests", status_code=status.HTTP_202_ACCEPTED)
    async def privacy_request(body: PrivacyRequestModel, request: Request) -> object:
        trusted = scope(request)
        return privacy.request(trusted.actor_id, PrivacyOperation(body.operation))

    @app.post("/api/v1/accounts/export", status_code=status.HTTP_202_ACCEPTED)
    async def export_account(request: Request) -> object:
        return privacy.request(scope(request).actor_id, PrivacyOperation.EXPORT)

    @app.post("/api/v1/accounts/correction", status_code=status.HTTP_202_ACCEPTED)
    async def correct_account(request: Request) -> object:
        return privacy.request(scope(request).actor_id, PrivacyOperation.CORRECTION)

    @app.post("/api/v1/accounts/deletion", status_code=status.HTTP_202_ACCEPTED)
    async def delete_account(request: Request) -> object:
        return privacy.request(scope(request).actor_id, PrivacyOperation.DELETION)

    @app.post("/api/v1/accounts/restriction", status_code=status.HTTP_202_ACCEPTED)
    async def restrict_account(request: Request) -> object:
        return privacy.request(scope(request).actor_id, PrivacyOperation.RESTRICTION)

    @app.post("/api/v1/accounts/legal-hold", status_code=status.HTTP_202_ACCEPTED)
    async def legal_hold(request: Request) -> object:
        return privacy.request(
            scope(request).actor_id, PrivacyOperation.LEGAL_HOLD, legal_hold=True
        )

    @app.get("/api/v1/privacy/requests/{request_id}")
    async def privacy_status(request_id: str) -> object:
        operation = privacy.requests.get(request_id)
        if operation is None:
            raise HTTPException(status_code=404, detail={"code": "privacy_request_not_found"})
        return operation

    @app.post("/api/v1/studios", status_code=status.HTTP_201_CREATED)
    async def create_studio(body: StudioCreateRequest, request: Request) -> object:
        trusted = scope(request)
        return tenancy.create_studio(trusted, body.name, body.slug)

    @app.post("/api/v1/studios/memberships", status_code=status.HTTP_201_CREATED)
    async def create_membership(body: MembershipRequest, request: Request) -> object:
        trusted = scope(request)
        return tenancy.create_membership(trusted, body.account_id, MembershipRole(body.role))

    @app.post("/api/v1/studios/invitations", status_code=status.HTTP_201_CREATED)
    async def invite_membership(body: InvitationRequest, request: Request) -> object:
        return admin.invite(scope(request), body.email, MembershipRole(body.role))

    @app.post("/api/v1/studios/memberships/role")
    async def change_membership_role(body: RoleChangeRequest, request: Request) -> object:
        return tenancy.change_role(scope(request), body.membership_id, MembershipRole(body.role))

    @app.post("/api/v1/studios/service-accounts", status_code=status.HTTP_201_CREATED)
    async def create_service_account(body: ServiceAccountRequest, request: Request) -> object:
        trusted = scope(request)
        return tenancy.create_service_account(trusted, body.name, frozenset(body.scopes))

    @app.post(
        "/api/v1/studios/service-accounts/revoke",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def revoke_service_account(request: Request, service_account_id: str) -> Response:
        tenancy.revoke_service_account(scope(request), service_account_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post(
        "/api/v1/sessions/revoke",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def revoke_session(request: Request) -> Response:
        trusted = scope(request)
        account = identity.accounts.get(trusted.actor_id)
        if account:
            account.session_epoch += 1
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/permissions/decision")
    async def decision(request: Request, action: str, resource_type: str) -> object:
        trusted = scope(request)
        result = policies.decide(
            PolicyRequest(
                Actor(
                    trusted.actor_id,
                    ActorKind.ACCOUNT,
                    trusted.studio_id,
                    trusted.roles,
                    mfa_verified=True,
                ),
                action,
                Resource(resource_type, None, trusted.studio_id),
                trusted.environment,
            )
        )
        return result

    return app


app = create_app()
