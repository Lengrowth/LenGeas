"""Versioned FastAPI composition root for Phase 03."""

from __future__ import annotations

from datetime import UTC
from typing import Annotated, Any, Protocol, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from packages.domain.audit.events import EventEnvelope
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

from .auth.guest import GuestIdentityService, TurnstileVerifier, UnconfiguredTurnstile
from .auth.jwt import JwtClaims
from .auth.mapping import InternalAccountMapper


class JwtVerifier(Protocol):
    async def verify(self, token: str) -> JwtClaims: ...


class UnconfiguredJwtVerifier:
    async def verify(self, token: str) -> JwtClaims:
        raise ValueError("authentication_provider_unconfigured")


class PersistenceUnavailable:
    """Fail-closed adapter used until an explicit Mongo composition is supplied."""

    def __init__(self) -> None:
        from threading import RLock

        self.accounts: dict[str, Any] = {}
        self.players: dict[str, Any] = {}
        self.identities: dict[str, Any] = {}
        self.profiles: dict[str, Any] = {}
        self.global_profiles: dict[str, Any] = {}
        self.audit: list[Any] = []
        self.events: list[Any] = []
        self.outbox: list[Any] = []
        self.lock = RLock()

    def _fail(self) -> None:
        raise RuntimeError("persistence_unconfigured")

    def __getattr__(self, name: str) -> Any:
        def fail(*args: Any, **kwargs: Any) -> Any:
            self._fail()

        return fail


bearer = HTTPBearer(auto_error=False)


def create_app(
    *,
    turnstile: TurnstileVerifier | None = None,
    jwt_verifier: JwtVerifier | None = None,
    identity: Any | None = None,
    tenancy: Any | None = None,
    test_mode: bool = False,
) -> FastAPI:
    app = FastAPI(
        title="LenGeas Identity and Tenancy API", version="1.0.0", openapi_version="3.1.0"
    )
    identity_repo = identity or (
        InMemoryIdentityRepository() if test_mode else PersistenceUnavailable()
    )
    tenancy_repo = tenancy or (
        InMemoryTenantRepository() if test_mode else PersistenceUnavailable()
    )
    identity_domain = cast(InMemoryIdentityRepository, identity_repo)
    tenancy_domain = cast(InMemoryTenantRepository, tenancy_repo)
    merge = MergeService(identity_domain)
    privacy = PrivacyService(identity_domain)
    policies = PolicyDecisionService()
    admin = StudioAdministration(tenancy_domain)
    guest = GuestIdentityService(identity_domain, turnstile or UnconfiguredTurnstile())
    verifier = jwt_verifier or UnconfiguredJwtVerifier()
    mapper = InternalAccountMapper(identity_domain)
    app.state.admin = admin
    app.state.identity = identity_repo
    app.state.tenancy = tenancy_repo
    app.state.guest = guest

    async def authenticate(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
    ) -> None:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail={"code": "authentication_required"})
        try:
            claims = await verifier.verify(credentials.credentials)
            account = mapper.map_subject(claims.subject)
        except (ValueError, KeyError, RuntimeError) as error:
            raise HTTPException(status_code=401, detail={"code": str(error)}) from error
        request.state.claims = claims
        request.state.account = account

    def scope(request: Request, *, game_id: str | None = None) -> TrustedScope:
        account = getattr(request.state, "account", None)
        studio_id = request.headers.get("x-studio-id")
        if account is None or not studio_id:
            raise HTTPException(status_code=401, detail={"code": "authentication_required"})
        membership = tenancy_repo.membership_for(studio_id, account.account_id)
        if membership is None or not membership.active:
            raise HTTPException(status_code=403, detail={"code": "membership_required"})
        if game_id and game_id not in membership.game_ids:
            raise HTTPException(status_code=403, detail={"code": "game_scope_mismatch"})
        claims = request.state.claims
        amr = claims.raw.get("amr", [])
        mfa_verified = claims.raw.get("aal") in {"aal2", "aal3"} or "mfa" in amr
        return TrustedScope(
            account.account_id,
            studio_id,
            game_id,
            Environment.TESTING,
            frozenset({membership.role}),
            mfa_verified=bool(mfa_verified),
            game_ids=membership.game_ids,
            environments=frozenset({Environment.TESTING}),
        )

    def authorize(
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        game_id: str | None = None,
    ) -> TrustedScope:
        trusted = scope(request, game_id=game_id)
        result = policies.decide(
            PolicyRequest(
                Actor(
                    trusted.actor_id,
                    ActorKind.ACCOUNT,
                    trusted.studio_id,
                    trusted.roles,
                    mfa_verified=trusted.mfa_verified,
                    game_ids=trusted.game_ids,
                    environments=trusted.environments,
                ),
                action,
                Resource(resource_type, resource_id, trusted.studio_id, game_id),
                trusted.environment,
            )
        )
        if not result.allowed:
            raise HTTPException(status_code=403, detail={"code": result.code})
        return trusted

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

    protected = [Depends(authenticate)]

    @app.post(
        "/api/v1/auth/identity-links", status_code=status.HTTP_201_CREATED, dependencies=protected
    )
    async def link_identity(body: IdentityLinkRequest, request: Request) -> dict[str, str]:
        trusted = authorize(request, "write", "identity")
        player = identity_repo.players.get(trusted.actor_id)
        if player is None:
            raise HTTPException(status_code=404, detail={"code": "player_not_found"})
        from packages.domain.identity.models import IdentityKind

        link = identity_repo.link_identity(
            player.player_id,
            IdentityKind.SUPABASE,
            body.provider,
            body.subject,
            account_id=trusted.actor_id,
        )
        identity_repo.emit(
            EventEnvelope.create(
                "identity.linked.v1",
                "api",
                studio_id=trusted.studio_id,
                player_id=player.player_id,
                payload={"provider": body.provider},
            )
        )
        return {"identity_id": link.identity_id, "player_id": link.player_id}

    @app.post("/api/v1/auth/credentials/rotate", dependencies=protected)
    async def rotate_credential(body: CredentialRotateRequest, request: Request) -> dict[str, str]:
        authorize(request, "write", "identity", body.identity_id)
        return {"refresh_token": guest.rotate(body.identity_id, body.refresh_token)}

    @app.get("/api/v1/auth/current", dependencies=protected)
    async def current_account(request: Request) -> object:
        account = request.state.account
        if account.deleted_at is not None:
            raise HTTPException(status_code=404, detail={"code": "account_not_found"})
        return account

    @app.post("/api/v1/players/merge/preview", dependencies=protected)
    async def merge_preview(body: MergePreviewRequest, request: Request) -> object:
        trusted = authorize(request, "write", "player", body.source_player_id)
        return merge.preview(trusted, body.source_player_id, body.target_player_id)

    @app.post("/api/v1/players/merge", dependencies=protected)
    async def merge_commit(body: MergeCommitRequest, request: Request) -> dict[str, str]:
        trusted = authorize(request, "write", "player")
        return {
            "player_id": merge.commit(trusted, body.preview_id, body.choices, body.idempotency_key)
        }

    @app.post(
        "/api/v1/privacy/requests", status_code=status.HTTP_202_ACCEPTED, dependencies=protected
    )
    async def privacy_request(body: PrivacyRequestModel, request: Request) -> object:
        trusted_id = request.state.account.account_id
        authorize(request, "write", "account", trusted_id)
        return privacy.request(trusted_id, PrivacyOperation(body.operation))

    for path, operation in (
        ("/api/v1/accounts/export", PrivacyOperation.EXPORT),
        ("/api/v1/accounts/correction", PrivacyOperation.CORRECTION),
        ("/api/v1/accounts/restriction", PrivacyOperation.RESTRICTION),
        ("/api/v1/accounts/legal-hold", PrivacyOperation.LEGAL_HOLD),
    ):

        async def rights(request: Request, op: PrivacyOperation = operation) -> object:
            trusted = authorize(request, "write", "account")
            return privacy.request(
                trusted.actor_id, op, legal_hold=op == PrivacyOperation.LEGAL_HOLD
            )

        app.add_api_route(
            path,
            rights,
            methods=["POST"],
            status_code=status.HTTP_202_ACCEPTED,
            dependencies=protected,
        )

    @app.post(
        "/api/v1/accounts/deletion", status_code=status.HTTP_202_ACCEPTED, dependencies=protected
    )
    async def delete_account(request: Request) -> object:
        trusted = authorize(request, "delete", "account")
        return privacy.request(trusted.actor_id, PrivacyOperation.DELETION)

    @app.get("/api/v1/privacy/requests/{request_id}", dependencies=protected)
    async def privacy_status(request_id: str, request: Request) -> object:
        trusted = authorize(request, "read", "privacy", request_id)
        operation = privacy.requests.get(request_id)
        if operation is None or operation.account_id != trusted.actor_id:
            raise HTTPException(status_code=404, detail={"code": "privacy_request_not_found"})
        return operation

    @app.post("/api/v1/studios", status_code=status.HTTP_201_CREATED, dependencies=protected)
    async def create_studio(body: StudioCreateRequest, request: Request) -> object:
        return tenancy_repo.create_studio(
            authorize(request, "admin", "studio"), body.name, body.slug
        )

    @app.post(
        "/api/v1/studios/memberships", status_code=status.HTTP_201_CREATED, dependencies=protected
    )
    async def create_membership(body: MembershipRequest, request: Request) -> object:
        return tenancy_repo.create_membership(
            authorize(request, "admin", "membership"), body.account_id, MembershipRole(body.role)
        )

    @app.post(
        "/api/v1/studios/invitations", status_code=status.HTTP_201_CREATED, dependencies=protected
    )
    async def invite_membership(body: InvitationRequest, request: Request) -> object:
        return admin.invite(
            authorize(request, "admin", "membership"), body.email, MembershipRole(body.role)
        )

    @app.post("/api/v1/studios/memberships/role", dependencies=protected)
    async def change_membership_role(body: RoleChangeRequest, request: Request) -> object:
        return tenancy_repo.change_role(
            authorize(request, "admin", "membership"), body.membership_id, MembershipRole(body.role)
        )

    @app.post(
        "/api/v1/studios/service-accounts",
        status_code=status.HTTP_201_CREATED,
        dependencies=protected,
    )
    async def create_service_account(body: ServiceAccountRequest, request: Request) -> object:
        return tenancy_repo.create_service_account(
            authorize(request, "admin", "service_account"), body.name, frozenset(body.scopes)
        )

    @app.post(
        "/api/v1/studios/service-accounts/revoke",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        dependencies=protected,
    )
    async def revoke_service_account(request: Request, service_account_id: str) -> Response:
        tenancy_repo.revoke_service_account(
            authorize(request, "admin", "service_account", service_account_id), service_account_id
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post(
        "/api/v1/sessions/revoke",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        dependencies=protected,
    )
    async def revoke_session(request: Request) -> Response:
        authorize(request, "write", "session")
        request.state.account.session_epoch += 1
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/permissions/decision", dependencies=protected)
    async def decision(
        request: Request, action: str, resource_type: str, game_id: str | None = None
    ) -> object:
        trusted = authorize(request, action, resource_type, game_id=game_id)
        return policies.decide(
            PolicyRequest(
                Actor(
                    trusted.actor_id,
                    ActorKind.ACCOUNT,
                    trusted.studio_id,
                    trusted.roles,
                    mfa_verified=trusted.mfa_verified,
                    game_ids=trusted.game_ids,
                    environments=trusted.environments,
                ),
                action,
                Resource(resource_type, None, trusted.studio_id, game_id),
                trusted.environment,
            )
        )

    return app


app = create_app()
