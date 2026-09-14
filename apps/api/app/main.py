"""Versioned FastAPI composition root for Phase 03."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Awaitable, Callable
from datetime import UTC
from typing import Annotated, Any, Protocol, cast

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
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
from packages.domain.coordination import IdempotencyStore, ProofConsumptionStore, RevocationStore
from packages.domain.coordination_memory import InMemoryIdempotencyStore
from packages.domain.identity.merge import MergeService
from packages.domain.identity.privacy import PrivacyOperation, PrivacyService
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.ids import new_uuid7
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


class ProviderIdentityVerifier(Protocol):
    async def verify(self, provider: str, subject: str, proof: str) -> bool: ...


class UnconfiguredProviderIdentityVerifier:
    async def verify(self, provider: str, subject: str, proof: str) -> bool:
        return False


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
    provider_verifier: ProviderIdentityVerifier | None = None,
    revocation_store: RevocationStore | None = None,
    proof_store: ProofConsumptionStore | None = None,
    idempotency_store: IdempotencyStore | None = None,
    test_mode: bool = False,
    allow_unconfigured: bool = False,
) -> FastAPI:
    if not test_mode and not allow_unconfigured and (identity is None or tenancy is None):
        raise RuntimeError("production_persistence_required")
    if not test_mode and not allow_unconfigured and (jwt_verifier is None or turnstile is None):
        raise RuntimeError("provider_configuration_required")
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
    guest = GuestIdentityService(
        identity_domain,
        turnstile or UnconfiguredTurnstile(),
        proof_store=proof_store,
    )
    verifier = jwt_verifier or UnconfiguredJwtVerifier()
    mapper = InternalAccountMapper(identity_domain)
    provider_control = provider_verifier or UnconfiguredProviderIdentityVerifier()
    mutation_idempotency = idempotency_store or (InMemoryIdempotencyStore() if test_mode else None)
    if not test_mode and not allow_unconfigured and mutation_idempotency is None:
        raise RuntimeError("idempotency_persistence_required")
    revoked_jtis: set[str] = set()
    revoked_subjects: set[str] = set()
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
            if claims.subject in revoked_subjects or (
                claims.jwt_id and claims.jwt_id in revoked_jtis
            ):
                raise ValueError("token_revoked")
            if revocation_store is not None:
                if claims.jwt_id and await revocation_store.is_jti_revoked(claims.jwt_id):
                    raise ValueError("token_revoked")
                if int(claims.raw.get("session_epoch", 0)) < await revocation_store.subject_epoch(
                    claims.subject
                ):
                    raise ValueError("token_revoked")
            account = mapper.map_subject(claims.subject)
        except (ValueError, KeyError, RuntimeError) as error:
            raise HTTPException(status_code=401, detail={"code": str(error)}) from error
        request.state.claims = claims
        request.state.account = account

    async def require_idempotency(
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    ) -> None:
        if not idempotency_key or len(idempotency_key) > 128:
            raise HTTPException(status_code=400, detail={"code": "idempotency_key_required"})

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

    def error_body(
        code: str, message: str, *, details: object = None, retryable: bool = False
    ) -> dict[str, object]:
        return {
            "error": {
                "code": code,
                "message": message,
                "request_id": new_uuid7(),
                "details": details or [],
                "retryable": retryable,
            }
        }

    @app.middleware("http")
    async def mutation_idempotency_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method != "POST" or mutation_idempotency is None:
            return await call_next(request)
        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)
        body = await request.body()
        actor = hashlib.sha256(
            request.headers.get("authorization", "anonymous").encode()
        ).hexdigest()
        tenant = request.headers.get("x-studio-id")
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "actor": actor,
                    "tenant": tenant,
                    "body": body.decode("utf-8", errors="replace"),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        try:
            existing = await mutation_idempotency.reserve(
                key=key,
                operation=f"{request.method}:{request.url.path}",
                actor_id=actor,
                tenant_id=tenant,
                fingerprint=fingerprint,
            )
        except ValueError as error:
            return JSONResponse(status_code=409, content=error_body(str(error), str(error)))
        if existing is not None:
            if existing.status_code is None:
                return JSONResponse(
                    status_code=409,
                    content=error_body("idempotency_in_progress", "Request is still in progress."),
                )
            if existing.status_code == status.HTTP_204_NO_CONTENT:
                return Response(status_code=existing.status_code)
            return JSONResponse(status_code=existing.status_code, content=existing.body)
        response = await call_next(request)
        body_iterator = getattr(response, "body_iterator", None)
        if body_iterator is None:
            response_body = response.body or b""
        else:
            chunks = [chunk async for chunk in body_iterator]
            response_body = b"".join(bytes(chunk) for chunk in chunks)
        if response.status_code < 500:
            try:
                stored_body = json.loads(bytes(response_body)) if response_body else None
                await mutation_idempotency.complete(
                    key, status_code=response.status_code, body=stored_body
                )
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                pass
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail if isinstance(error.detail, dict) else {"code": str(error.detail)}
        return JSONResponse(
            status_code=error.status_code,
            content=error_body(
                str(detail.get("code", "request_failed")),
                str(detail.get("message", detail.get("code", "Request failed."))),
                details=detail.get("details", []),
                retryable=bool(detail.get("retryable", False)),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                "validation_error",
                "Request validation failed.",
                details=jsonable_encoder(error.errors()),
            ),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=409, content=error_body(str(error), str(error)))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"service": "platform-api", "status": "ok"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {"service": "platform-api", "version": "0.3.0", "status": "ok"}

    @app.post(
        "/api/v1/auth/guests",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_idempotency)],
    )
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

    protected = [Depends(authenticate), Depends(require_idempotency)]
    protected_read = [Depends(authenticate)]

    @app.post(
        "/api/v1/auth/identity-links", status_code=status.HTTP_201_CREATED, dependencies=protected
    )
    async def link_identity(body: IdentityLinkRequest, request: Request) -> dict[str, str]:
        trusted = authorize(request, "write", "identity")
        player_id = request.state.account.player_id
        player = identity_repo.players.get(player_id) if player_id else None
        if player is None:
            raise HTTPException(status_code=404, detail={"code": "player_not_found"})
        if not body.provider_proof or not await provider_control.verify(
            body.provider, body.subject, body.provider_proof
        ):
            raise HTTPException(status_code=403, detail={"code": "provider_control_required"})
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

    @app.get("/api/v1/auth/current", dependencies=protected_read)
    async def current_account(request: Request) -> object:
        account = request.state.account
        if account.deleted_at is not None:
            raise HTTPException(status_code=404, detail={"code": "account_not_found"})
        return account

    @app.post("/api/v1/players/merge/preview", dependencies=protected)
    async def merge_preview(body: MergePreviewRequest, request: Request) -> object:
        trusted = authorize(request, "write", "player", body.source_player_id)
        if request.state.account.player_id not in {body.source_player_id, body.target_player_id}:
            raise HTTPException(status_code=403, detail={"code": "merge_owner_required"})
        if not body.source_credential or not body.target_credential:
            raise HTTPException(status_code=403, detail={"code": "merge_proof_required"})
        if not guest.prove_player(
            body.source_player_id, body.source_credential
        ) or not guest.prove_player(body.target_player_id, body.target_credential):
            raise HTTPException(status_code=403, detail={"code": "merge_proof_invalid"})
        return merge.preview(trusted, body.source_player_id, body.target_player_id)

    @app.post("/api/v1/players/merge", dependencies=protected)
    async def merge_commit(body: MergeCommitRequest, request: Request) -> dict[str, str]:
        trusted = authorize(request, "write", "player")
        if request.headers.get("Idempotency-Key") != body.idempotency_key:
            raise HTTPException(status_code=400, detail={"code": "idempotency_key_mismatch"})
        if not body.source_credential or not body.target_credential:
            raise HTTPException(status_code=403, detail={"code": "merge_proof_required"})
        preview = merge.previews.get(body.preview_id)
        if preview is None or request.state.account.player_id not in {
            preview.source_player_id,
            preview.target_player_id,
        }:
            raise HTTPException(status_code=403, detail={"code": "merge_owner_required"})
        if not guest.prove_player(
            preview.source_player_id, body.source_credential
        ) or not guest.prove_player(preview.target_player_id, body.target_credential):
            raise HTTPException(status_code=403, detail={"code": "merge_proof_invalid"})
        return {
            "player_id": merge.commit(trusted, body.preview_id, body.choices, body.idempotency_key)
        }

    @app.post(
        "/api/v1/privacy/requests", status_code=status.HTTP_202_ACCEPTED, dependencies=protected
    )
    async def privacy_request(body: PrivacyRequestModel, request: Request) -> object:
        trusted_id = request.state.account.account_id
        authorize(request, "write", "account", trusted_id)
        trusted = scope(request)
        return privacy.request(
            trusted_id, PrivacyOperation(body.operation), studio_id=trusted.studio_id
        )

    for path, operation in (
        ("/api/v1/accounts/export", PrivacyOperation.EXPORT),
        ("/api/v1/accounts/correction", PrivacyOperation.CORRECTION),
        ("/api/v1/accounts/restriction", PrivacyOperation.RESTRICTION),
        ("/api/v1/accounts/legal-hold", PrivacyOperation.LEGAL_HOLD),
    ):

        async def rights(request: Request, op: PrivacyOperation = operation) -> object:
            trusted = authorize(request, "write", "account")
            return privacy.request(
                trusted.actor_id,
                op,
                legal_hold=op == PrivacyOperation.LEGAL_HOLD,
                studio_id=trusted.studio_id,
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
        return privacy.request(
            trusted.actor_id, PrivacyOperation.DELETION, studio_id=trusted.studio_id
        )

    @app.get("/api/v1/privacy/requests/{request_id}", dependencies=protected_read)
    async def privacy_status(request_id: str, request: Request) -> object:
        trusted = authorize(request, "read", "privacy", request_id)
        operation = privacy.requests.get(request_id)
        if operation is None:
            load_privacy = getattr(identity_repo, "privacy_request_for", None)
            if load_privacy is not None:
                operation = load_privacy(request_id)
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
        account = tenancy_repo.create_service_account(
            authorize(request, "admin", "service_account"), body.name, frozenset(body.scopes)
        )
        credential = getattr(tenancy_repo, "service_credentials", {}).get(
            account.service_account_id
        )
        return {
            "service_account_id": account.service_account_id,
            "client_id": account.client_id,
            "credential": credential,
            "scopes": sorted(account.scopes),
        }

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
        save_account = getattr(identity_repo, "save_account", None)
        if save_account is not None:
            save_account(request.state.account)
        claims = request.state.claims
        if claims.jwt_id:
            revoked_jtis.add(claims.jwt_id)
            revoke_jti = getattr(verifier, "revoke_jti", None)
            if revoke_jti:
                result = revoke_jti(claims.jwt_id)
                if inspect.isawaitable(result):
                    await result
            elif revocation_store is not None:
                await revocation_store.revoke_jti(claims.jwt_id)
        revoked_subjects.add(claims.subject)
        revoke_subject = getattr(verifier, "revoke_subject", None)
        if revoke_subject:
            result = revoke_subject(claims.subject)
            if inspect.isawaitable(result):
                await result
        elif revocation_store is not None:
            await revocation_store.revoke_subject(
                claims.subject, request.state.account.session_epoch
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/permissions/decision", dependencies=protected_read)
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


def _build_application() -> FastAPI:
    from .composition import create_production_app

    return create_production_app()


app = _build_application()
