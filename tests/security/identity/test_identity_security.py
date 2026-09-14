from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from packages.domain.authorization.policy import (
    Actor,
    ActorKind,
    PolicyDecisionService,
    PolicyRequest,
    Resource,
)
from packages.domain.tenancy.models import Environment, MembershipRole


class IdentitySecurityTests(unittest.TestCase):
    def test_forged_tenant_scope_is_denied(self) -> None:
        actor = Actor(
            "a", ActorKind.ACCOUNT, "studio-a", frozenset({MembershipRole.ADMIN}), mfa_verified=True
        )
        request = PolicyRequest(
            actor, "write", Resource("studio", "s", "studio-b"), Environment.TESTING
        )
        self.assertEqual(PolicyDecisionService().decide(request).code, "tenant_mismatch")

    def test_expired_support_grant_and_mfa_bypass_are_denied(self) -> None:
        expired = Actor(
            "a",
            ActorKind.ACCOUNT,
            "studio-a",
            frozenset({MembershipRole.SUPPORT}),
            support_case_id="c",
            support_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        decision = PolicyDecisionService().decide(
            PolicyRequest(expired, "read", Resource("player", "p", "studio-a"), Environment.TESTING)
        )
        self.assertEqual(decision.code, "support_grant_expired")
        operator = Actor(
            "a",
            ActorKind.ACCOUNT,
            "studio-a",
            frozenset({MembershipRole.ADMIN}),
            mfa_verified=False,
        )
        decision = PolicyDecisionService().decide(
            PolicyRequest(
                operator, "admin", Resource("studio", "s", "studio-a"), Environment.TESTING
            )
        )
        self.assertEqual(decision.code, "mfa_required")
