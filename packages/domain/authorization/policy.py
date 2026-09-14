"""Deterministic RBAC/ABAC decisions with machine-readable explanations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from packages.domain.tenancy.models import Environment, MembershipRole


class ActorKind(StrEnum):
    ACCOUNT = "account"
    SERVICE = "service"
    AI_AGENT = "ai_agent"


@dataclass(frozen=True, slots=True)
class Actor:
    actor_id: str
    kind: ActorKind
    studio_id: str | None
    roles: frozenset[MembershipRole] = frozenset()
    scopes: frozenset[str] = frozenset()
    mfa_verified: bool = False
    support_case_id: str | None = None
    support_expires_at: datetime | None = None
    game_ids: frozenset[str] = frozenset()
    environments: frozenset[Environment] = frozenset()
    support_grant_valid: bool = False


@dataclass(frozen=True, slots=True)
class Resource:
    resource_type: str
    resource_id: str | None
    studio_id: str | None
    game_id: str | None = None
    owner_id: str | None = None
    sensitivity: str = "normal"


@dataclass(frozen=True, slots=True)
class PolicyRequest:
    actor: Actor
    action: str
    resource: Resource
    environment: Environment
    now: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    code: str
    explanation: str
    obligations: tuple[str, ...] = ()


class PolicyDecisionService:
    ROLE_ACTIONS: dict[MembershipRole, frozenset[str]] = {
        MembershipRole.OWNER: frozenset(
            {"read", "write", "admin", "delete", "publish", "support_sensitive"}
        ),
        MembershipRole.ADMIN: frozenset({"read", "write", "admin", "delete", "support_sensitive"}),
        MembershipRole.DEVELOPER: frozenset({"read", "write"}),
        MembershipRole.DESIGNER: frozenset({"read", "write"}),
        MembershipRole.WRITER: frozenset({"read", "write"}),
        MembershipRole.ANALYST: frozenset({"read"}),
        MembershipRole.SUPPORT: frozenset({"read"}),
        MembershipRole.VIEWER: frozenset({"read"}),
        MembershipRole.AI_AGENT: frozenset({"read", "draft_write"}),
    }

    def decide(self, request: PolicyRequest) -> Decision:
        actor, resource = request.actor, request.resource
        if actor.studio_id is None or resource.studio_id != actor.studio_id:
            return Decision(False, "tenant_mismatch", "actor and resource are in different studios")
        if actor.environments and request.environment not in actor.environments:
            return Decision(
                False, "environment_scope_mismatch", "actor is not scoped to this environment"
            )
        if resource.game_id is not None and resource.game_id not in actor.game_ids:
            return Decision(False, "game_scope_mismatch", "actor is not scoped to this game")
        if (
            actor.kind == ActorKind.SERVICE
            and f"{resource.resource_type}:{request.action}" not in actor.scopes
        ):
            return Decision(
                False, "service_scope_missing", "service account scope does not cover action"
            )
        if actor.kind == ActorKind.AI_AGENT and request.action not in {"read", "draft_write"}:
            return Decision(False, "ai_publish_forbidden", "AI agents may not approve or publish")
        if (
            resource.game_id is not None
            and request.action != "read"
            and actor.kind == ActorKind.ACCOUNT
            and resource.owner_id not in {None, actor.actor_id}
        ):
            return Decision(False, "ownership_required", "resource is owned by another actor")
        if (
            actor.support_case_id
            and actor.support_expires_at
            and request.now >= actor.support_expires_at
        ):
            return Decision(False, "support_grant_expired", "support grant is expired")
        if (
            actor.roles & {MembershipRole.OWNER, MembershipRole.ADMIN}
            and not actor.mfa_verified
            and request.action in {"admin", "delete", "publish", "support_sensitive"}
        ):
            return Decision(False, "mfa_required", "operator action requires recent MFA")
        if (
            MembershipRole.SUPPORT in actor.roles
            and request.action == "support_sensitive"
            and (actor.support_case_id is None or not actor.support_grant_valid)
        ):
            return Decision(False, "support_case_required", "support access requires an open case")
        actions = set().union(*(self.ROLE_ACTIONS.get(role, frozenset()) for role in actor.roles))
        if request.action not in actions:
            return Decision(False, "role_denied", "role does not grant this action")
        obligations = ("redact_pii",) if MembershipRole.SUPPORT in actor.roles else ()
        return Decision(
            True, "allow", "role, tenant, environment, and resource attributes matched", obligations
        )
