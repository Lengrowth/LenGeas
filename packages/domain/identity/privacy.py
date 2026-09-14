"""Account rights lifecycle with non-authenticating tombstones."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from packages.domain.audit.events import EventEnvelope
from packages.domain.ids import new_uuid7

from .repository import InMemoryIdentityRepository


class PrivacyOperation(StrEnum):
    EXPORT = "export"
    CORRECTION = "correction"
    DELETION = "deletion"
    RESTRICTION = "restriction"
    LEGAL_HOLD = "legal_hold"


@dataclass(frozen=True, slots=True)
class PrivacyRequest:
    request_id: str
    account_id: str
    operation: PrivacyOperation
    requested_at: datetime
    status: str
    legal_hold: bool = False


class PrivacyService:
    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository
        self.requests: dict[str, PrivacyRequest] = {}
        self.financial_history: dict[str, dict[str, str]] = {}
        self.deleted_tombstones: set[str] = set()
        self.legal_holds: set[str] = set()

    def request(
        self, account_id: str, operation: PrivacyOperation, *, legal_hold: bool = False
    ) -> PrivacyRequest:
        account = self.repository.accounts.get(account_id)
        if account is None:
            raise KeyError("account_not_found")
        if operation == PrivacyOperation.DELETION and legal_hold:
            raise ValueError("legal_hold_conflict")
        if operation == PrivacyOperation.DELETION and account_id in self.legal_holds:
            raise ValueError("legal_hold_conflict")
        request = PrivacyRequest(
            new_uuid7(), account_id, operation, datetime.now(UTC), "queued", legal_hold
        )
        self.requests[request.request_id] = request
        self.repository.record_audit(
            account_id, "privacy.requested", None, account_id, {"operation": operation.value}
        )
        self.repository.emit(
            EventEnvelope.create(
                "privacy.requested.v1",
                "PrivacyService",
                payload={"operation": operation.value},
            )
        )
        if operation == PrivacyOperation.LEGAL_HOLD:
            self.legal_holds.add(account_id)
            return self._complete(request)
        if operation in {
            PrivacyOperation.EXPORT,
            PrivacyOperation.CORRECTION,
            PrivacyOperation.RESTRICTION,
        }:
            return self.execute(request.request_id)
        return request

    def _complete(self, request: PrivacyRequest) -> PrivacyRequest:
        completed = PrivacyRequest(
            request.request_id,
            request.account_id,
            request.operation,
            request.requested_at,
            "completed",
            request.legal_hold,
        )
        self.requests[request.request_id] = completed
        return completed

    def execute(self, request_id: str) -> PrivacyRequest:
        request = self.requests[request_id]
        account = self.repository.accounts[request.account_id]
        if request.operation == PrivacyOperation.RESTRICTION:
            account.restricted = True
        elif request.operation == PrivacyOperation.CORRECTION:
            account.session_epoch += 1
        elif request.operation == PrivacyOperation.EXPORT:
            self.financial_history.setdefault(request.account_id, {})
        return self._complete(request)

    def execute_deletion(self, request_id: str) -> PrivacyRequest:
        request = self.requests[request_id]
        if request.operation != PrivacyOperation.DELETION:
            raise ValueError("not_deletion")
        if request.account_id in self.legal_holds:
            raise ValueError("legal_hold_conflict")
        account = self.repository.accounts[request.account_id]
        account.deleted_at = datetime.now(UTC)
        account.email_hash = None
        account.session_epoch += 1
        self.deleted_tombstones.add(request.account_id)
        for identity in self.repository.identities.values():
            if identity.account_id == request.account_id:
                identity.revoked_at = datetime.now(UTC)
                player = self.repository.players.get(identity.player_id)
                if player is not None:
                    player.tombstone = True
        retained = self.financial_history.get(request.account_id)
        if retained:
            pseudonym = "deleted_" + hashlib.sha256(request.account_id.encode()).hexdigest()[:24]
            retained["account_ref"] = pseudonym
        return self._complete(request)
