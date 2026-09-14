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
    studio_id: str | None = None


class PrivacyService:
    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository
        self.requests: dict[str, PrivacyRequest] = repository.privacy_requests
        self.financial_history: dict[str, dict[str, str]] = repository.financial_history
        self.deleted_tombstones: set[str] = set()
        self.legal_holds: set[str] = set()

    def request(
        self,
        account_id: str,
        operation: PrivacyOperation,
        *,
        legal_hold: bool = False,
        studio_id: str | None = None,
    ) -> PrivacyRequest:
        account = self.repository.accounts.get(account_id)
        if account is None:
            raise KeyError("account_not_found")
        if operation == PrivacyOperation.DELETION and legal_hold:
            raise ValueError("legal_hold_conflict")
        if operation == PrivacyOperation.DELETION and account_id in self.legal_holds:
            raise ValueError("legal_hold_conflict")
        request = PrivacyRequest(
            new_uuid7(), account_id, operation, datetime.now(UTC), "queued", legal_hold, studio_id
        )
        self.requests[request.request_id] = request
        persist_request = getattr(self.repository, "persist_privacy_request", None)
        if persist_request is not None:
            persist_request(request)
        self.repository.record_audit(
            account_id,
            "privacy.requested",
            studio_id,
            account_id,
            {"operation": operation.value, "status": "queued"},
        )
        self.repository.emit(
            EventEnvelope.create(
                "privacy.requested.v1",
                "PrivacyService",
                studio_id=studio_id,
                player_id=getattr(account, "player_id", None),
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
            request.studio_id,
        )
        self.requests[request.request_id] = completed
        persist_completion = getattr(self.repository, "persist_privacy_completion", None)
        if persist_completion is not None:
            persist_completion(completed)
        self.repository.record_audit(
            request.account_id,
            "privacy.completed",
            request.studio_id,
            request.account_id,
            {"operation": request.operation.value, "status": "completed"},
        )
        self.repository.emit(
            EventEnvelope.create(
                "privacy.completed.v1",
                "PrivacyService",
                studio_id=request.studio_id,
                payload={"operation": request.operation.value, "status": "completed"},
            )
        )
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
        self.repository.begin()
        try:
            account = self.repository.accounts[request.account_id]
            account.deleted_at = datetime.now(UTC)
            account.email_hash = None
            account.session_epoch += 1
            for identity in self.repository.identities.values():
                if identity.account_id == request.account_id:
                    identity.revoked_at = datetime.now(UTC)
                    player = self.repository.players.get(identity.player_id)
                    if player is not None:
                        player.tombstone = True
            pseudonym = "deleted_" + hashlib.sha256(request.account_id.encode()).hexdigest()[:24]
            retained = self.financial_history.setdefault(request.account_id, {})
            retained["account_ref"] = pseudonym
            persist_financial = getattr(self.repository, "persist_financial_record", None)
            if persist_financial is not None:
                persist_financial(
                    request.studio_id,
                    request.account_id,
                    pseudonym,
                    request.request_id,
                )
            completed = self._complete(request)
            self.repository.commit()
            self.deleted_tombstones.add(request.account_id)
            return completed
        except Exception:
            self.repository.rollback()
            raise
