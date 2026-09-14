"""Tenant-scoped repository contracts and a deterministic test repository."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from packages.domain.audit.events import EventEnvelope
from packages.domain.ids import new_uuid7

from .models import Invitation, Membership, MembershipRole, ServiceAccount, Studio, TrustedScope


def _id() -> str:
    return new_uuid7()


ALLOWED_SERVICE_SCOPES = frozenset(
    {"studio:read", "studio:write", "player:read", "player:write", "profile:read", "profile:write"}
)


class TenantRepository(Protocol):
    def get_studio(self, scope: TrustedScope, studio_id: str) -> Studio | None: ...

    def list_memberships(self, scope: TrustedScope) -> list[Membership]: ...

    def create_studio(self, scope: TrustedScope, name: str, slug: str) -> Studio: ...

    def create_membership(
        self, scope: TrustedScope, account_id: str, role: MembershipRole
    ) -> Membership: ...

    def create_service_account(
        self, scope: TrustedScope, name: str, scopes: frozenset[str]
    ) -> ServiceAccount: ...


class InMemoryTenantRepository:
    """Small repository used by unit and provider-independent integration tests."""

    def __init__(self) -> None:
        self.studios: dict[str, Studio] = {}
        self.memberships: dict[str, Membership] = {}
        self.invitations: dict[str, Invitation] = {}
        self.service_accounts: dict[str, ServiceAccount] = {}
        self._client_ids: set[str] = set()
        self.audit: list[dict[str, str]] = []
        self.events: list[EventEnvelope] = []
        self.service_credentials: dict[str, str] = {}

    @staticmethod
    def _check(scope: TrustedScope, studio_id: str) -> None:
        if scope.studio_id != studio_id:
            raise PermissionError("tenant_scope_mismatch")

    def get_studio(self, scope: TrustedScope, studio_id: str) -> Studio | None:
        self._check(scope, studio_id)
        return self.studios.get(studio_id)

    def list_memberships(self, scope: TrustedScope) -> list[Membership]:
        return [m for m in self.memberships.values() if m.studio_id == scope.studio_id]

    def membership_for(self, studio_id: str, account_id: str) -> Membership | None:
        return next(
            (
                m
                for m in self.memberships.values()
                if m.studio_id == studio_id and m.account_id == account_id
            ),
            None,
        )

    def create_studio(self, scope: TrustedScope, name: str, slug: str) -> Studio:
        if not scope.mfa_verified and MembershipRole.ADMIN in scope.roles:
            raise PermissionError("mfa_required")
        now = datetime.now(UTC)
        studio = Studio(_id(), name, slug, now)
        self.studios[studio.studio_id] = studio
        return studio

    def create_membership(
        self, scope: TrustedScope, account_id: str, role: MembershipRole
    ) -> Membership:
        if (
            account_id != scope.actor_id
            and MembershipRole.OWNER not in scope.roles
            and MembershipRole.ADMIN not in scope.roles
        ):
            raise PermissionError("membership_admin_required")
        if any(
            m.account_id == account_id and m.studio_id == scope.studio_id
            for m in self.memberships.values()
        ):
            raise ValueError("membership_exists")
        membership = Membership(_id(), scope.studio_id, account_id, role, datetime.now(UTC))
        self.memberships[membership.membership_id] = membership
        self.events.append(
            EventEnvelope.create(
                "studio.service_account_revoked.v1",
                "InMemoryTenantRepository",
                studio_id=scope.studio_id,
                payload={"membership_id": membership.membership_id, "role": role.value},
            )
        )
        return membership

    def change_role(
        self, scope: TrustedScope, membership_id: str, role: MembershipRole
    ) -> Membership:
        membership = self.memberships.get(membership_id)
        if membership is None or membership.studio_id != scope.studio_id:
            raise KeyError("membership_not_found")
        if MembershipRole.OWNER not in scope.roles and MembershipRole.ADMIN not in scope.roles:
            raise PermissionError("membership_admin_required")
        membership.role = role
        self.events.append(
            EventEnvelope.create(
                "studio.membership_changed.v1",
                "InMemoryTenantRepository",
                studio_id=scope.studio_id,
                payload={"membership_id": membership_id, "role": role.value},
            )
        )
        return membership

    def create_service_account(
        self, scope: TrustedScope, name: str, scopes: frozenset[str]
    ) -> ServiceAccount:
        if not ({MembershipRole.OWNER, MembershipRole.ADMIN} & set(scope.roles)):
            raise PermissionError("service_account_admin_required")
        if not scope.mfa_verified:
            raise PermissionError("mfa_required")
        if not scopes or not scopes <= ALLOWED_SERVICE_SCOPES:
            raise ValueError("service_scope_not_allowed")
        client_id = "svc_" + new_uuid7().replace("-", "")
        if client_id in self._client_ids:
            raise ValueError("service_client_id_exists")
        self._client_ids.add(client_id)
        credential = secrets.token_urlsafe(32)
        account = ServiceAccount(
            _id(),
            scope.studio_id,
            client_id,
            name,
            scopes,
            datetime.now(UTC),
            credential_hash=hashlib.sha256(credential.encode()).hexdigest(),
        )
        self.service_credentials[account.service_account_id] = credential
        self.service_accounts[account.service_account_id] = account
        self.audit.append(
            {"action": "studio.membership_changed.v1", "subject_id": account.service_account_id}
        )
        self.events.append(
            EventEnvelope.create(
                "studio.membership_changed.v1",
                "InMemoryTenantRepository",
                studio_id=scope.studio_id,
                payload={"service_account_id": account.service_account_id},
            )
        )
        return account

    def revoke_service_account(self, scope: TrustedScope, service_account_id: str) -> None:
        account = self.service_accounts.get(service_account_id)
        if account is None or account.studio_id != scope.studio_id:
            raise KeyError("service_account_not_found")
        if not ({MembershipRole.OWNER, MembershipRole.ADMIN} & set(scope.roles)):
            raise PermissionError("service_account_admin_required")
        account.revoked_at = datetime.now(UTC)
        self.audit.append(
            {"action": "studio.membership_changed.v1", "subject_id": service_account_id}
        )
        self.events.append(
            EventEnvelope.create(
                "studio.membership_changed.v1",
                "InMemoryTenantRepository",
                studio_id=scope.studio_id,
                payload={"service_account_id": service_account_id, "action": "revoked"},
            )
        )

    def verify_service_credential(self, service_account_id: str, credential: str) -> bool:
        account = self.service_accounts.get(service_account_id)
        return bool(
            account
            and account.revoked_at is None
            and account.credential_hash
            and account.credential_hash == hashlib.sha256(credential.encode()).hexdigest()
        )

    def all_studios(self) -> Iterable[Studio]:
        return self.studios.values()
