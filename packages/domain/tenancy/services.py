"""Studio administration orchestration."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from packages.domain.audit.events import EventEnvelope
from packages.domain.ids import new_uuid7

from .models import Invitation, MembershipRole, TrustedScope
from .repository import InMemoryTenantRepository


class StudioAdministration:
    def __init__(self, repository: InMemoryTenantRepository) -> None:
        self.repository = repository

    def invite(
        self, scope: TrustedScope, email: str, role: MembershipRole, *, ttl_hours: int = 72
    ) -> Invitation:
        if not email or len(email.encode()) > 320:
            raise ValueError("invalid_email")
        if role == MembershipRole.OWNER:
            raise ValueError("owner_invitation_forbidden")
        digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        now = datetime.now(UTC)
        invitation = Invitation(
            invitation_id=new_uuid7(),
            studio_id=scope.studio_id,
            email_hash=digest,
            role=role,
            expires_at=now + timedelta(hours=max(1, min(ttl_hours, 168))),
            created_at=now,
        )
        self.repository.invitations[invitation.invitation_id] = invitation
        self.repository.audit.append(
            {"action": "studio.membership_changed.v1", "subject_id": invitation.invitation_id}
        )
        self.repository.events.append(
            EventEnvelope.create(
                "studio.membership_changed.v1",
                "StudioAdministration",
                studio_id=scope.studio_id,
                payload={"invitation_id": invitation.invitation_id, "role": role.value},
            )
        )
        return invitation

    def enforce_mfa(self, scope: TrustedScope) -> int:
        changed = 0
        for membership in self.repository.list_memberships(scope):
            if membership.role in {
                MembershipRole.OWNER,
                MembershipRole.ADMIN,
                MembershipRole.SUPPORT,
            }:
                membership.mfa_required = True
                changed += 1
        return changed
