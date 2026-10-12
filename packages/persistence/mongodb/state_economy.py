"""MongoDB transaction adapters for state, ledger, actions, and purchases."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, cast

from pymongo.errors import DuplicateKeyError

from packages.domain.economy import (
    INT64_MAX,
    INT64_MIN,
    EconomyAction,
    EconomyError,
    plan_economy_entries,
)
from packages.domain.entitlements import EntitlementKind, VerifiedPurchase
from packages.domain.ids import new_uuid7
from packages.domain.inventory import (
    InventoryError,
    InventoryRewardGrant,
    plan_inventory_grant,
)
from packages.domain.player_state import _merge_patch, validate_patch


class MongoEconomyRepository:
    """Commits state changes, ledger postings, receipts, idempotency, and outbox atomically."""

    def __init__(self, database: Any) -> None:
        self.database = database
        self.ledger = database.economy_ledger
        self.states = database.player_states
        self.receipts = database.action_receipts
        self.idempotency = database.idempotency_records
        self.outbox = database.outbox_events
        self.entitlements = database.entitlements
        self.inventories = database.inventories
        self.audit_logs = database.audit_logs

    async def ensure_indexes(self) -> None:
        await self.states.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("namespace_id", 1)],
            unique=True,
            name="uq_player_state_namespace",
        )
        await self.ledger.create_index(
            [("record_type", 1), ("transaction_id", 1)],
            unique=True,
            partialFilterExpression={"record_type": "transaction"},
            name="uq_ledger_transaction",
        )
        await self.ledger.create_index(
            [
                ("record_type", 1),
                ("studio_id", 1),
                ("game_id", 1),
                ("account_id", 1),
                ("asset_id", 1),
            ],
            unique=True,
            partialFilterExpression={"record_type": "balance_projection"},
            name="uq_ledger_balance_projection",
        )
        await self.ledger.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("occurred_at", -1)],
            name="ledger_player_time",
        )
        await self.idempotency.create_index(
            [
                ("studio_id", 1),
                ("game_id", 1),
                ("player_id", 1),
                ("actor_id", 1),
                ("idempotency_key", 1),
            ],
            unique=True,
            name="uq_action_idempotency_scope",
        )
        await self.idempotency.create_index(
            [("provider", 1), ("provider_transaction_id", 1)],
            unique=True,
            partialFilterExpression={"provider_transaction_id": {"$type": "string"}},
            name="uq_permanent_provider_transaction",
        )
        await self.receipts.create_index("receipt_id", unique=True, name="uq_action_receipt_id")
        await self.outbox.create_index("event_id", unique=True, name="uq_outbox_event_id")
        await self.entitlements.create_index(
            [("provider", 1), ("provider_transaction_id", 1)],
            unique=True,
            name="uq_entitlement_provider_transaction",
        )
        await self.entitlements.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("status", 1)],
            name="entitlement_player_status",
        )

    @staticmethod
    def _scoped(scope: dict[str, str]) -> dict[str, str]:
        return {key: scope[key] for key in ("studio_id", "game_id", "player_id")}

    async def execute_action(
        self,
        *,
        studio_id: str,
        game_id: str,
        player_id: str,
        game_profile_id: str,
        actor_id: str,
        action_id: str,
        expected_state_version: int,
        state_patch: dict[str, Any],
        action: EconomyAction,
        idempotency_key: str,
        definition_digest: str,
        inventory_grants: tuple[InventoryRewardGrant, ...] = (),
    ) -> dict[str, Any]:
        if (
            isinstance(expected_state_version, bool)
            or expected_state_version < 0
            or not idempotency_key
            or not game_profile_id
        ):
            raise EconomyError("economy_action_precondition_failed")
        validate_patch(state_patch)
        scope = {"studio_id": studio_id, "game_id": game_id, "player_id": player_id}
        namespace_id = "economy"
        payload = {
            "action_id": action_id,
            "expected_state_version": expected_state_version,
            "state_patch": state_patch,
            "economy_action": asdict(action),
            "inventory_grants": [
                {
                    "studio_id": grant.scope.studio_id,
                    "game_id": grant.scope.game_id,
                    "player_id": grant.scope.player_id,
                    "game_profile_id": grant.scope.game_profile_id,
                    "container_id": grant.scope.container_id,
                    "item_id": grant.definition.item_id,
                    "stackable": grant.definition.stackable,
                    "max_stack": grant.definition.max_stack,
                    "quantity": grant.quantity,
                    "expected_version": grant.expected_version,
                    "attributes": dict(grant.attributes),
                }
                for grant in inventory_grants
            ],
            "definition_digest": definition_digest,
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        idem_query = {**scope, "actor_id": actor_id, "idempotency_key": idempotency_key}
        try:
            async with await self.database.client.start_session() as session:
                async with session.start_transaction():
                    previous = await self.idempotency.find_one(idem_query, session=session)
                    if previous is not None:
                        if previous.get("fingerprint") != fingerprint:
                            raise EconomyError("idempotency_conflict")
                        return cast(dict[str, Any], previous["response"])
                    state_query = {**scope, "namespace_id": namespace_id}
                    state_doc = await self.states.find_one(state_query, session=session)
                    version = int(state_doc.get("state_version", 0)) if state_doc else 0
                    if version != expected_state_version:
                        raise EconomyError("state_conflict")
                    current_state = dict(state_doc.get("data", {})) if state_doc else {}
                    next_state = _merge_patch(current_state, state_patch)
                    state_bytes = json.dumps(
                        next_state, sort_keys=True, separators=(",", ":"), allow_nan=False
                    ).encode()
                    if len(state_bytes) > 6 * 1024 * 1024:
                        raise EconomyError("state_document_too_large")
                    assets = set(action.costs) | set(action.grants)
                    assets.update(target for target, _, _ in action.overflow_routes.values())
                    player_accounts = {asset: f"player:{player_id}:{asset}" for asset in assets}
                    balances: dict[str, int] = {}
                    for asset, account in player_accounts.items():
                        projection = await self.ledger.find_one(
                            {
                                "record_type": "balance_projection",
                                "studio_id": studio_id,
                                "game_id": game_id,
                                "account_id": account,
                                "asset_id": asset,
                            },
                            session=session,
                        )
                        if projection is not None and projection.get("quarantined"):
                            raise EconomyError("balance_projection_quarantined")
                        balances[asset] = int(projection.get("balance", 0)) if projection else 0
                    lines = plan_economy_entries(action, balances, player_id=player_id)
                    if not lines:
                        raise EconomyError("empty_economy_action")
                    totals: dict[tuple[str, str], int] = {}
                    for account, asset, amount in lines:
                        key = (account, asset)
                        totals[key] = totals.get(key, 0) + amount
                    projected: dict[tuple[str, str], int] = {}
                    for (account, asset), amount in totals.items():
                        projection_query = {
                            "record_type": "balance_projection",
                            "studio_id": studio_id,
                            "game_id": game_id,
                            "account_id": account,
                            "asset_id": asset,
                        }
                        projection = await self.ledger.find_one(projection_query, session=session)
                        balance = (int(projection.get("balance", 0)) if projection else 0) + amount
                        if balance < INT64_MIN or balance > INT64_MAX:
                            raise EconomyError("balance_overflow")
                        if account.startswith("player:") and balance < 0:
                            raise EconomyError("insufficient_balance")
                        projected[(account, asset)] = balance
                    now = datetime.now(UTC)
                    transaction_id = new_uuid7()
                    entry_docs = [
                        {
                            "entry_id": new_uuid7(),
                            "account_id": account,
                            "asset_id": asset,
                            "amount": amount,
                            "balance_after": projected[(account, asset)],
                        }
                        for account, asset, amount in lines
                    ]
                    ledger_doc = {
                        "record_type": "transaction",
                        "transaction_id": transaction_id,
                        **scope,
                        "actor_id": actor_id,
                        "action_id": action_id,
                        "idempotency_key": idempotency_key,
                        "reason": action_id,
                        "source": "player_action",
                        "definition_digest": definition_digest,
                        "entries": entry_docs,
                        "occurred_at": now,
                    }
                    await self.ledger.insert_one(ledger_doc, session=session)
                    for (account, asset), balance in projected.items():
                        query = {
                            "record_type": "balance_projection",
                            "studio_id": studio_id,
                            "game_id": game_id,
                            "account_id": account,
                            "asset_id": asset,
                        }
                        await self.ledger.replace_one(
                            query,
                            {
                                **query,
                                "balance": balance,
                                "updated_at": now,
                                "state_version": (
                                    await self.ledger.find_one(query, session=session) or {}
                                ).get("state_version", 0)
                                + 1,
                            },
                            upsert=True,
                            session=session,
                        )
                    inventory_results: list[dict[str, Any]] = []
                    granted_containers: set[str] = set()
                    for grant in inventory_grants:
                        inventory_scope = grant.scope
                        if (
                            inventory_scope.studio_id != studio_id
                            or inventory_scope.game_id != game_id
                            or inventory_scope.player_id != player_id
                            or inventory_scope.game_profile_id != game_profile_id
                            or isinstance(grant.expected_version, bool)
                            or not isinstance(grant.expected_version, int)
                            or grant.expected_version < 0
                            or isinstance(grant.quantity, bool)
                            or not isinstance(grant.quantity, int)
                            or grant.quantity < 1
                            or inventory_scope.container_id in granted_containers
                        ):
                            raise InventoryError("inventory_reward_scope_mismatch")
                        granted_containers.add(inventory_scope.container_id)
                        inventory_query = {
                            "studio_id": studio_id,
                            "game_id": game_id,
                            "player_id": player_id,
                            "container_id": inventory_scope.container_id,
                        }
                        inventory = await self.inventories.find_one(
                            inventory_query, session=session
                        )
                        if inventory is None:
                            raise InventoryError("inventory_not_found")
                        if int(inventory.get("state_version", -1)) != grant.expected_version:
                            raise InventoryError("inventory_conflict")
                        from packages.persistence.mongodb.inventory import MongoInventoryRepository

                        current_inventory = MongoInventoryRepository._snapshot(inventory)
                        updated_inventory = plan_inventory_grant(
                            current_inventory,
                            grant.definition,
                            grant.quantity,
                            grant.attributes,
                        )
                        prior_ids = {
                            str(item["instance_id"]) for item in inventory.get("instances", [])
                        }
                        next_ids = {item.instance_id for item in updated_inventory.instances}
                        result = await self.inventories.replace_one(
                            {**inventory_query, "state_version": grant.expected_version},
                            MongoInventoryRepository._document(updated_inventory),
                            session=session,
                        )
                        if result.modified_count != 1:
                            raise InventoryError("inventory_conflict")
                        await self.audit_logs.insert_one(
                            {
                                "audit_id": new_uuid7(),
                                **inventory_query,
                                "game_profile_id": inventory_scope.game_profile_id,
                                "event_type": "inventory.item_history.v1",
                                "operation": "grant",
                                "item_id": grant.definition.item_id,
                                "quantity": grant.quantity,
                                "instance_ids": sorted(prior_ids.symmetric_difference(next_ids)),
                                "idempotency_key": idempotency_key,
                                "actor_id": actor_id,
                                "occurred_at": now,
                            },
                            session=session,
                        )
                        inventory_results.append(
                            {
                                "container_id": inventory_scope.container_id,
                                "state_version": updated_inventory.state_version,
                            }
                        )
                    state_doc_out = {
                        **state_query,
                        "state_id": state_doc.get("state_id", new_uuid7())
                        if state_doc
                        else new_uuid7(),
                        "game_profile_id": game_profile_id,
                        "state_version": version + 1,
                        "data": next_state,
                        "updated_at": now,
                    }
                    if state_doc is None:
                        await self.states.insert_one(state_doc_out, session=session)
                    else:
                        updated = await self.states.replace_one(
                            {**state_query, "state_version": expected_state_version},
                            state_doc_out,
                            session=session,
                        )
                        if updated.modified_count != 1:
                            raise EconomyError("state_conflict")
                    receipt_id, event_id = new_uuid7(), new_uuid7()
                    response = {
                        "receipt_id": receipt_id,
                        "transaction_id": transaction_id,
                        "status": "committed",
                        "state_version": version + 1,
                        "state_patch": state_patch,
                        "balances": {
                            asset: projected.get((account, asset), balances.get(asset, 0))
                            for asset, account in player_accounts.items()
                        },
                        "event_ids": [event_id],
                        "inventories": inventory_results,
                    }
                    await self.receipts.insert_one(
                        {
                            "receipt_id": receipt_id,
                            **scope,
                            "actor_id": actor_id,
                            "transaction_id": transaction_id,
                            "action_id": action_id,
                            "idempotency_key": idempotency_key,
                            "response": response,
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    await self.idempotency.insert_one(
                        {
                            **idem_query,
                            "fingerprint": fingerprint,
                            "response": response,
                            "created_at": now,
                        },
                        session=session,
                    )
                    await self.outbox.insert_one(
                        {
                            "event_id": event_id,
                            "event_type": "economy.action_committed.v1",
                            **scope,
                            "transaction_id": transaction_id,
                            "receipt_id": receipt_id,
                            "status": "pending",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    return response
        except DuplicateKeyError as error:
            previous = await self.idempotency.find_one(idem_query)
            if previous is not None and previous.get("fingerprint") == fingerprint:
                return cast(dict[str, Any], previous["response"])
            raise EconomyError("idempotency_conflict") from error

    async def fulfill_purchase(
        self,
        purchase: VerifiedPurchase,
        *,
        actor_id: str,
        kind: EntitlementKind,
        idempotency_key: str,
        quantity: int = 1,
    ) -> dict[str, Any]:
        if quantity < 1:
            raise EconomyError("invalid_purchase_quantity")
        provider_key = {
            "provider": purchase.provider,
            "provider_transaction_id": purchase.provider_transaction_id,
        }
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
        now = datetime.now(UTC)
        try:
            async with await self.database.client.start_session() as session:
                async with session.start_transaction():
                    existing = await self.idempotency.find_one(provider_key, session=session)
                    if existing is not None:
                        if existing.get("fingerprint") != fingerprint:
                            raise EconomyError("provider_transaction_conflict")
                        return cast(dict[str, Any], existing["response"])
                    entitlement_id, receipt_id, event_id = new_uuid7(), new_uuid7(), new_uuid7()
                    entitlement = {
                        "entitlement_id": entitlement_id,
                        "studio_id": purchase.studio_id,
                        "game_id": purchase.game_id,
                        "player_id": purchase.player_id,
                        "product_id": purchase.product_id,
                        "kind": kind,
                        "status": "active",
                        "provider": purchase.provider,
                        "provider_transaction_id": purchase.provider_transaction_id,
                        "purchased_at": purchase.purchased_at,
                        "granted_at": now,
                        "expires_at": purchase.expires_at,
                        "quantity_remaining": quantity if kind == "consumable" else 1,
                    }
                    response = {
                        "receipt_id": receipt_id,
                        "entitlement_id": entitlement_id,
                        "status": "fulfilled",
                        "provider": purchase.provider,
                        "provider_transaction_id": purchase.provider_transaction_id,
                    }
                    await self.entitlements.insert_one(entitlement, session=session)
                    await self.receipts.insert_one(
                        {
                            "receipt_id": receipt_id,
                            "studio_id": purchase.studio_id,
                            "game_id": purchase.game_id,
                            "player_id": purchase.player_id,
                            "actor_id": actor_id,
                            "provider": purchase.provider,
                            "provider_transaction_id": purchase.provider_transaction_id,
                            "entitlement_id": entitlement_id,
                            "status": "fulfilled",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    await self.idempotency.insert_one(
                        {
                            **provider_key,
                            "studio_id": purchase.studio_id,
                            "game_id": purchase.game_id,
                            "player_id": purchase.player_id,
                            "actor_id": actor_id,
                            "idempotency_key": idempotency_key,
                            "fingerprint": fingerprint,
                            "response": response,
                            "created_at": now,
                            "permanent": True,
                        },
                        session=session,
                    )
                    await self.outbox.insert_one(
                        {
                            "event_id": event_id,
                            "event_type": "entitlement.granted.v1",
                            "studio_id": purchase.studio_id,
                            "game_id": purchase.game_id,
                            "player_id": purchase.player_id,
                            "entitlement_id": entitlement_id,
                            "receipt_id": receipt_id,
                            "status": "pending",
                            "occurred_at": now,
                        },
                        session=session,
                    )
                    return response
        except DuplicateKeyError as error:
            existing = await self.idempotency.find_one(provider_key)
            if existing is not None and existing.get("fingerprint") == fingerprint:
                return cast(dict[str, Any], existing["response"])
            raise EconomyError("provider_transaction_conflict") from error

    async def revoke_purchase(
        self,
        provider: str,
        provider_transaction_id: str,
        *,
        reason: str,
        provider_event_id: str | None = None,
        payload_digest: str | None = None,
    ) -> dict[str, Any]:
        if reason not in {"refund", "chargeback", "provider_revocation"}:
            raise EconomyError("invalid_revocation_reason")
        if bool(provider_event_id) != bool(payload_digest):
            raise EconomyError("webhook_identity_required")
        webhook_scope = {
            "studio_id": "provider_webhook",
            "game_id": provider,
            "player_id": "provider",
            "actor_id": f"provider:{provider}",
            "idempotency_key": provider_event_id,
        }
        webhook_fingerprint = hashlib.sha256(
            f"{payload_digest}|{provider_transaction_id}|{reason}".encode()
        ).hexdigest()
        async with await self.database.client.start_session() as session:
            async with session.start_transaction():
                if provider_event_id and payload_digest:
                    previous = await self.idempotency.find_one(webhook_scope, session=session)
                    if previous is not None:
                        if previous.get("fingerprint") != webhook_fingerprint:
                            raise EconomyError("webhook_replay_conflict")
                        return cast(dict[str, Any], previous["response"])
                purchase = await self.entitlements.find_one(
                    {"provider": provider, "provider_transaction_id": provider_transaction_id},
                    session=session,
                )
                if purchase is None:
                    raise EconomyError("purchase_not_found")
                if purchase.get("status") == "revoked":
                    return {
                        "entitlement_id": purchase["entitlement_id"],
                        "status": "revoked",
                        "event_id": None,
                    }
                now = datetime.now(UTC)
                changed = await self.entitlements.update_one(
                    {"entitlement_id": purchase["entitlement_id"], "status": "active"},
                    {"$set": {"status": "revoked", "revoked_at": now, "revocation_reason": reason}},
                    session=session,
                )
                if changed.modified_count != 1:
                    raise EconomyError("entitlement_conflict")
                event_id = new_uuid7()
                response = {
                    "entitlement_id": purchase["entitlement_id"],
                    "status": "revoked",
                    "event_id": event_id,
                }
                await self.outbox.insert_one(
                    {
                        "event_id": event_id,
                        "event_type": "entitlement.revoked.v1",
                        "studio_id": purchase["studio_id"],
                        "game_id": purchase["game_id"],
                        "player_id": purchase["player_id"],
                        "entitlement_id": purchase["entitlement_id"],
                        "reason": reason,
                        "status": "pending",
                        "occurred_at": now,
                    },
                    session=session,
                )
                if provider_event_id and payload_digest:
                    await self.idempotency.insert_one(
                        {
                            **webhook_scope,
                            "fingerprint": webhook_fingerprint,
                            "response": response,
                            "created_at": now,
                            "action_class": "provider_webhook",
                        },
                        session=session,
                    )
                return response

    async def consume_entitlement(self, entitlement_id: str, quantity: int = 1) -> dict[str, Any]:
        if quantity < 1:
            raise EconomyError("invalid_consumption_quantity")
        async with await self.database.client.start_session() as session:
            async with session.start_transaction():
                current = await self.entitlements.find_one(
                    {"entitlement_id": entitlement_id, "kind": "consumable", "status": "active"},
                    session=session,
                )
                if current is None or int(current.get("quantity_remaining", 0)) < quantity:
                    raise EconomyError("consumable_entitlement_unavailable")
                remaining = int(current["quantity_remaining"]) - quantity
                status = "consumed" if remaining == 0 else "active"
                updated = await self.entitlements.update_one(
                    {
                        "entitlement_id": entitlement_id,
                        "status": "active",
                        "quantity_remaining": current["quantity_remaining"],
                    },
                    {
                        "$set": {
                            "quantity_remaining": remaining,
                            "status": status,
                            "updated_at": datetime.now(UTC),
                        }
                    },
                    session=session,
                )
                if updated.modified_count != 1:
                    raise EconomyError("entitlement_conflict")
                return {
                    "entitlement_id": entitlement_id,
                    "quantity_remaining": remaining,
                    "status": status,
                }

    async def expire_due_entitlements(self, *, now: datetime | None = None) -> int:
        current_time = now or datetime.now(UTC)
        expired = [
            document
            async for document in self.entitlements.find(
                {"status": "active", "expires_at": {"$lte": current_time}}
            )
        ]
        if not expired:
            return 0
        changed = 0
        async with await self.database.client.start_session() as session:
            async with session.start_transaction():
                for item in expired:
                    result = await self.entitlements.update_one(
                        {"entitlement_id": item["entitlement_id"], "status": "active"},
                        {"$set": {"status": "expired", "expired_at": current_time}},
                        session=session,
                    )
                    if result.modified_count:
                        changed += 1
                        await self.outbox.insert_one(
                            {
                                "event_id": new_uuid7(),
                                "event_type": "entitlement.expired.v1",
                                "studio_id": item["studio_id"],
                                "game_id": item["game_id"],
                                "player_id": item["player_id"],
                                "entitlement_id": item["entitlement_id"],
                                "status": "pending",
                                "occurred_at": current_time,
                            },
                            session=session,
                        )
        return changed
