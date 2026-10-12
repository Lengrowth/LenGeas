"""Permanent provider purchase idempotency and server-side entitlement lifecycle."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from packages.domain.ids import new_uuid7

EntitlementKind = Literal["permanent", "consumable", "subscription"]
EntitlementStatus = Literal["active", "revoked", "expired", "consumed"]


class EntitlementError(ValueError):
    """A purchase or entitlement transition failed validation."""


@dataclass(frozen=True, slots=True)
class VerifiedPurchase:
    provider: Literal["apple", "google"]
    provider_transaction_id: str
    product_id: str
    player_id: str
    game_id: str
    studio_id: str
    purchased_at: datetime
    expires_at: datetime | None
    environment: Literal["sandbox", "production"]


@dataclass(frozen=True, slots=True)
class Entitlement:
    entitlement_id: str
    studio_id: str
    game_id: str
    player_id: str
    product_id: str
    kind: EntitlementKind
    status: EntitlementStatus
    provider: str
    provider_transaction_id: str
    granted_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    quantity_remaining: int = 1


@dataclass(frozen=True, slots=True)
class PurchaseReceipt:
    receipt_id: str
    provider: str
    provider_transaction_id: str
    entitlement_id: str
    idempotency_key: str
    status: str
    created_at: datetime


class InMemoryEntitlementRepository:
    """Concurrency-safe model for the durable Mongo provider-id unique index."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._provider_transactions: dict[tuple[str, str], tuple[str, PurchaseReceipt]] = {}
        self._entitlements: dict[str, Entitlement] = {}
        self._receipts: dict[str, PurchaseReceipt] = {}
        self._webhook_ids: dict[tuple[str, str], str] = {}

    def fulfill(
        self,
        purchase: VerifiedPurchase,
        *,
        kind: EntitlementKind,
        idempotency_key: str,
        quantity: int = 1,
    ) -> tuple[PurchaseReceipt, Entitlement]:
        if not purchase.provider_transaction_id or not idempotency_key or quantity < 1:
            raise EntitlementError("purchase_idempotency_required")
        unique_key = (purchase.provider, purchase.provider_transaction_id)
        fingerprint = "|".join(
            (
                purchase.studio_id,
                purchase.game_id,
                purchase.player_id,
                purchase.product_id,
                kind,
                str(quantity),
            )
        )
        with self._lock:
            existing = self._provider_transactions.get(unique_key)
            if existing is not None:
                if existing[0] != fingerprint:
                    raise EntitlementError("provider_transaction_conflict")
                receipt = existing[1]
                entitlement = self._entitlements[receipt.entitlement_id]
                return receipt, entitlement
            if purchase.expires_at is not None and purchase.expires_at <= purchase.purchased_at:
                raise EntitlementError("purchase_expiry_invalid")
            entitlement = Entitlement(
                new_uuid7(),
                purchase.studio_id,
                purchase.game_id,
                purchase.player_id,
                purchase.product_id,
                kind,
                "active",
                purchase.provider,
                purchase.provider_transaction_id,
                datetime.now(UTC),
                purchase.expires_at,
                quantity_remaining=quantity if kind == "consumable" else 1,
            )
            receipt = PurchaseReceipt(
                new_uuid7(),
                purchase.provider,
                purchase.provider_transaction_id,
                entitlement.entitlement_id,
                idempotency_key,
                "fulfilled",
                datetime.now(UTC),
            )
            self._provider_transactions[unique_key] = (fingerprint, receipt)
            self._entitlements[entitlement.entitlement_id] = entitlement
            self._receipts[receipt.receipt_id] = receipt
            return receipt, entitlement

    def revoke(
        self,
        provider: str,
        provider_transaction_id: str,
        *,
        reason: Literal["refund", "chargeback", "provider_revocation"],
    ) -> Entitlement:
        with self._lock:
            found = self._provider_transactions.get((provider, provider_transaction_id))
            if found is None:
                raise EntitlementError("purchase_not_found")
            prior = self._entitlements[found[1].entitlement_id]
            if prior.status == "revoked":
                return prior
            updated = Entitlement(
                prior.entitlement_id,
                prior.studio_id,
                prior.game_id,
                prior.player_id,
                prior.product_id,
                prior.kind,
                "revoked",
                prior.provider,
                prior.provider_transaction_id,
                prior.granted_at,
                prior.expires_at,
                datetime.now(UTC),
                reason,
                prior.quantity_remaining,
            )
            self._entitlements[prior.entitlement_id] = updated
            return updated

    def accept_webhook(self, provider: str, event_id: str, payload_digest: str) -> bool:
        if not event_id or not payload_digest:
            raise EntitlementError("webhook_identity_required")
        key = (provider, event_id)
        with self._lock:
            previous = self._webhook_ids.get(key)
            if previous is not None:
                if previous != payload_digest:
                    raise EntitlementError("webhook_replay_conflict")
                return False
            self._webhook_ids[key] = payload_digest
            return True

    def entitlements(self, studio_id: str, game_id: str, player_id: str) -> tuple[Entitlement, ...]:
        with self._lock:
            now = datetime.now(UTC)
            return tuple(
                entitlement
                for entitlement in self._entitlements.values()
                if entitlement.studio_id == studio_id
                and entitlement.game_id == game_id
                and entitlement.player_id == player_id
                and entitlement.status == "active"
                and (entitlement.expires_at is None or entitlement.expires_at > now)
            )

    def all_entitlements(self) -> tuple[Entitlement, ...]:
        with self._lock:
            return tuple(self._entitlements.values())

    def consume(self, entitlement_id: str, quantity: int = 1) -> Entitlement:
        if quantity < 1:
            raise EntitlementError("invalid_consumption_quantity")
        with self._lock:
            prior = self._entitlements.get(entitlement_id)
            if prior is None or prior.kind != "consumable" or prior.status != "active":
                raise EntitlementError("consumable_entitlement_unavailable")
            if prior.quantity_remaining < quantity:
                raise EntitlementError("insufficient_entitlement_quantity")
            remaining = prior.quantity_remaining - quantity
            updated = Entitlement(
                prior.entitlement_id,
                prior.studio_id,
                prior.game_id,
                prior.player_id,
                prior.product_id,
                prior.kind,
                "consumed" if remaining == 0 else "active",
                prior.provider,
                prior.provider_transaction_id,
                prior.granted_at,
                prior.expires_at,
                prior.revoked_at,
                prior.revocation_reason,
                remaining,
            )
            self._entitlements[entitlement_id] = updated
            return updated

    def expire_due(self, now: datetime | None = None) -> tuple[Entitlement, ...]:
        current_time = now or datetime.now(UTC)
        with self._lock:
            expired: list[Entitlement] = []
            for entitlement_id, prior in tuple(self._entitlements.items()):
                if (
                    prior.status == "active"
                    and prior.expires_at is not None
                    and prior.expires_at <= current_time
                ):
                    updated = Entitlement(
                        prior.entitlement_id,
                        prior.studio_id,
                        prior.game_id,
                        prior.player_id,
                        prior.product_id,
                        prior.kind,
                        "expired",
                        prior.provider,
                        prior.provider_transaction_id,
                        prior.granted_at,
                        prior.expires_at,
                        prior.revoked_at,
                        prior.revocation_reason,
                        prior.quantity_remaining,
                    )
                    self._entitlements[entitlement_id] = updated
                    expired.append(updated)
            return tuple(expired)
