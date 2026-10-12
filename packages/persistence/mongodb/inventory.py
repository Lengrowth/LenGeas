"""MongoDB container persistence with optimistic updates and audit history."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from packages.domain.ids import new_uuid7
from packages.domain.inventory import (
    InMemoryInventoryRepository,
    InventoryError,
    InventoryScope,
    InventorySnapshot,
    ItemDefinition,
    plan_inventory_consume,
    plan_inventory_equip,
    plan_inventory_grant,
)


class MongoInventoryRepository:
    def __init__(self, database: Any) -> None:
        self.inventories = database.inventories
        self.audit_logs = database.audit_logs
        self.idempotency = database.idempotency_records
        self.client = database.client

    async def ensure_indexes(self) -> None:
        await self.inventories.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("container_id", 1)],
            unique=True,
            name="uq_inventory_container_scope",
        )
        await self.inventories.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1)],
            name="inventory_player_scope",
        )
        await self.audit_logs.create_index(
            [("studio_id", 1), ("game_id", 1), ("player_id", 1), ("occurred_at", -1)],
            name="item_history_scope_time",
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

    @staticmethod
    def _scope(scope: InventoryScope) -> dict[str, str]:
        return {
            "studio_id": scope.studio_id,
            "game_id": scope.game_id,
            "player_id": scope.player_id,
            "container_id": scope.container_id,
        }

    @classmethod
    def _snapshot(cls, raw: dict[str, Any]) -> InventorySnapshot:
        from packages.domain.inventory import ItemInstance, ItemStack

        scope = InventoryScope(
            raw["studio_id"],
            raw["game_id"],
            raw["player_id"],
            raw["game_profile_id"],
            raw["container_id"],
        )
        return InventorySnapshot(
            scope,
            int(raw["state_version"]),
            int(raw["capacity_slots"]),
            tuple(ItemStack(**stack) for stack in raw.get("stacks", [])),
            tuple(ItemInstance(**item) for item in raw.get("instances", [])),
            raw.get("equipment", {}),
        )

    @staticmethod
    def _document(snapshot: InventorySnapshot) -> dict[str, Any]:
        scope = snapshot.scope
        return {
            **MongoInventoryRepository._scope(scope),
            "game_profile_id": scope.game_profile_id,
            "state_version": snapshot.state_version,
            "capacity_slots": snapshot.capacity_slots,
            "stacks": [
                {
                    "stack_id": item.stack_id,
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "attributes": dict(item.attributes),
                }
                for item in snapshot.stacks
            ],
            "instances": [
                {
                    "instance_id": item.instance_id,
                    "item_id": item.item_id,
                    "attributes": dict(item.attributes),
                }
                for item in snapshot.instances
            ],
            "equipment": dict(snapshot.equipment),
            "updated_at": datetime.now(UTC),
        }

    async def create(self, snapshot: InventorySnapshot) -> None:
        if snapshot.state_version != 0:
            raise InventoryError("new_inventory_version_invalid")
        try:
            await self.inventories.insert_one(self._document(snapshot))
        except DuplicateKeyError as error:
            raise InventoryError("inventory_exists") from error

    async def read(self, scope: InventoryScope) -> InventorySnapshot | None:
        raw = await self.inventories.find_one(self._scope(scope))
        if raw is not None and raw.get("quarantined"):
            raise InventoryError("inventory_quarantined")
        return self._snapshot(raw) if raw is not None else None

    async def commit(
        self,
        snapshot: InventorySnapshot,
        *,
        expected_version: int,
        operation: str,
        item_id: str,
        quantity: int,
        idempotency_key: str,
        actor_id: str,
        related_player_id: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> InventorySnapshot:
        try:
            return await self._commit_transaction(
                snapshot,
                expected_version=expected_version,
                operation=operation,
                item_id=item_id,
                quantity=quantity,
                idempotency_key=idempotency_key,
                actor_id=actor_id,
                related_player_id=related_player_id,
                details=details,
            )
        except DuplicateKeyError as error:
            fingerprint = self._mutation_fingerprint(
                operation=operation,
                item_id=item_id,
                quantity=quantity,
                expected_version=expected_version,
                related_player_id=related_player_id,
                details=details,
            )
            previous = await self.idempotency.find_one(
                {
                    **self._scope(snapshot.scope),
                    "actor_id": actor_id,
                    "idempotency_key": idempotency_key,
                }
            )
            if previous is not None and previous.get("fingerprint") == fingerprint:
                return self._snapshot(previous["snapshot"])
            raise InventoryError("idempotency_conflict") from error

    async def _commit_transaction(
        self,
        snapshot: InventorySnapshot,
        *,
        expected_version: int,
        operation: str,
        item_id: str,
        quantity: int,
        idempotency_key: str,
        actor_id: str,
        related_player_id: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> InventorySnapshot:
        if not idempotency_key or not actor_id or quantity < 0:
            raise InventoryError("inventory_mutation_metadata_invalid")
        if snapshot.state_version != expected_version + 1:
            raise InventoryError("inventory_version_invalid")
        scope = snapshot.scope
        scoped = self._scope(scope)
        query = {**scoped, "state_version": expected_version}
        idem_query = {**scoped, "actor_id": actor_id, "idempotency_key": idempotency_key}
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "operation": operation,
                    "item_id": item_id,
                    "quantity": quantity,
                    "expected_version": expected_version,
                    "related_player_id": related_player_id,
                    "details": dict(details or {}),
                },
                sort_keys=True,
                default=str,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        now = datetime.now(UTC)
        history_id = new_uuid7()
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                previous = await self.idempotency.find_one(idem_query, session=session)
                if previous is not None:
                    if previous.get("fingerprint") != fingerprint:
                        raise InventoryError("idempotency_conflict")
                    return self._snapshot(previous["snapshot"])
                prior_inventory = await self.inventories.find_one(query, session=session)
                if prior_inventory is None:
                    raise InventoryError("inventory_conflict")
                prior_instance_ids = {
                    str(item["instance_id"]) for item in prior_inventory.get("instances", [])
                }
                next_instance_ids = {item.instance_id for item in snapshot.instances}
                updated = await self.inventories.replace_one(
                    query, self._document(snapshot), session=session
                )
                if updated.modified_count != 1:
                    raise InventoryError("inventory_conflict")
                await self.audit_logs.insert_one(
                    {
                        "audit_id": history_id,
                        "studio_id": scope.studio_id,
                        "game_id": scope.game_id,
                        "player_id": scope.player_id,
                        "game_profile_id": scope.game_profile_id,
                        "container_id": scope.container_id,
                        "event_type": "inventory.item_history.v1",
                        "operation": operation,
                        "item_id": item_id,
                        "quantity": quantity,
                        "instance_ids": sorted(
                            prior_instance_ids.symmetric_difference(next_instance_ids)
                        ),
                        "idempotency_key": idempotency_key,
                        "related_player_id": related_player_id,
                        "occurred_at": now,
                    },
                    session=session,
                )
                await self.idempotency.insert_one(
                    {
                        **idem_query,
                        "fingerprint": fingerprint,
                        "snapshot": self._document(snapshot),
                        "created_at": now,
                        "action_class": "inventory",
                    },
                    session=session,
                )
        return snapshot

    @staticmethod
    def _mutation_fingerprint(
        *,
        operation: str,
        item_id: str,
        quantity: int,
        expected_version: int,
        related_player_id: str | None,
        details: Mapping[str, Any] | None,
    ) -> str:
        return hashlib.sha256(
            json.dumps(
                {
                    "operation": operation,
                    "item_id": item_id,
                    "quantity": quantity,
                    "expected_version": expected_version,
                    "related_player_id": related_player_id,
                    "details": dict(details or {}),
                },
                sort_keys=True,
                default=str,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    async def _mutation_base(
        self,
        scope: InventoryScope,
        *,
        expected_version: int,
        operation: str,
        item_id: str,
        quantity: int,
        idempotency_key: str,
        actor_id: str,
        details: Mapping[str, Any] | None = None,
    ) -> tuple[InventorySnapshot | None, str]:
        if not idempotency_key or not actor_id or quantity < 0:
            raise InventoryError("inventory_mutation_metadata_invalid")
        fingerprint = self._mutation_fingerprint(
            operation=operation,
            item_id=item_id,
            quantity=quantity,
            expected_version=expected_version,
            related_player_id=None,
            details=details,
        )
        previous = await self.idempotency.find_one(
            {**self._scope(scope), "actor_id": actor_id, "idempotency_key": idempotency_key}
        )
        if previous is not None:
            if previous.get("fingerprint") != fingerprint:
                raise InventoryError("idempotency_conflict")
            return self._snapshot(previous["snapshot"]), fingerprint
        current = await self.read(scope)
        if current is None:
            raise InventoryError("inventory_not_found")
        if current.state_version != expected_version:
            raise InventoryError("inventory_conflict")
        return current, fingerprint

    async def grant(
        self,
        scope: InventoryScope,
        definition: ItemDefinition,
        quantity: int,
        *,
        expected_version: int,
        idempotency_key: str,
        actor_id: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> InventorySnapshot:
        details = {
            "attributes": dict(attributes or {}),
            "stackable": definition.stackable,
            "max_stack": definition.max_stack,
        }
        current, _ = await self._mutation_base(
            scope,
            expected_version=expected_version,
            operation="grant",
            item_id=definition.item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
            details=details,
        )
        if current is not None and current.state_version != expected_version:
            return current
        assert current is not None
        if current.state_version == expected_version + 1:
            return current
        updated = plan_inventory_grant(current, definition, quantity, attributes)
        return await self.commit(
            updated,
            expected_version=expected_version,
            operation="grant",
            item_id=definition.item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
            details=details,
        )

    async def consume(
        self,
        scope: InventoryScope,
        item_id: str,
        quantity: int,
        *,
        expected_version: int,
        idempotency_key: str,
        actor_id: str,
    ) -> InventorySnapshot:
        current, _ = await self._mutation_base(
            scope,
            expected_version=expected_version,
            operation="consume",
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
        )
        assert current is not None
        if current.state_version != expected_version:
            return current
        updated = plan_inventory_consume(current, item_id, quantity)
        return await self.commit(
            updated,
            expected_version=expected_version,
            operation="consume",
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
        )

    async def equip(
        self,
        scope: InventoryScope,
        instance_id: str,
        slot: str,
        definition: ItemDefinition,
        *,
        expected_version: int,
        idempotency_key: str,
        actor_id: str,
    ) -> InventorySnapshot:
        details = {"instance_id": instance_id, "slot": slot}
        current, _ = await self._mutation_base(
            scope,
            expected_version=expected_version,
            operation="equip",
            item_id=definition.item_id,
            quantity=1,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
            details=details,
        )
        assert current is not None
        if current.state_version != expected_version:
            return current
        updated = plan_inventory_equip(current, instance_id, slot, definition)
        return await self.commit(
            updated,
            expected_version=expected_version,
            operation="equip",
            item_id=definition.item_id,
            quantity=1,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
            details=details,
        )

    async def history(self, scope: InventoryScope, *, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise InventoryError("invalid_history_limit")
        cursor = self.audit_logs.find(self._scope(scope)).sort("occurred_at", -1).limit(limit)
        return [event async for event in cursor]

    async def transfer(
        self,
        source_scope: InventoryScope,
        target_scope: InventoryScope,
        item_id: str,
        quantity: int,
        definition: ItemDefinition,
        *,
        source_version: int,
        target_version: int,
        idempotency_key: str,
        actor_id: str,
    ) -> tuple[InventorySnapshot, InventorySnapshot]:
        if not actor_id or not idempotency_key:
            raise InventoryError("inventory_mutation_metadata_invalid")
        fingerprint = (
            f"transfer:{target_scope.player_id}:{item_id}:{quantity}:"
            f"{definition.stackable}:{definition.max_stack}:{definition.transferable}"
        )
        source_idem = {
            **self._scope(source_scope),
            "actor_id": actor_id,
            "idempotency_key": idempotency_key,
        }
        target_idem = {
            **self._scope(target_scope),
            "actor_id": actor_id,
            "idempotency_key": idempotency_key,
        }
        try:
            async with await self.client.start_session() as session:
                async with session.start_transaction():
                    previous_source = await self.idempotency.find_one(source_idem, session=session)
                    previous_target = await self.idempotency.find_one(target_idem, session=session)
                    if previous_source is not None or previous_target is not None:
                        if (
                            previous_source is None
                            or previous_target is None
                            or previous_source.get("fingerprint") != fingerprint
                            or previous_target.get("fingerprint") != fingerprint
                        ):
                            raise InventoryError("idempotency_conflict")
                        return (
                            self._snapshot(previous_source["snapshot"]),
                            self._snapshot(previous_target["snapshot"]),
                        )
                    source_raw = await self.inventories.find_one(
                        self._scope(source_scope), session=session
                    )
                    target_raw = await self.inventories.find_one(
                        self._scope(target_scope), session=session
                    )
                    if source_raw is None or target_raw is None:
                        raise InventoryError("inventory_not_found")
                    source = self._snapshot(source_raw)
                    target = self._snapshot(target_raw)
                    if (
                        source.state_version != source_version
                        or target.state_version != target_version
                    ):
                        raise InventoryError("inventory_conflict")
                    source_after, target_after = (
                        InMemoryInventoryRepository.plan_transfer_snapshots(
                            source, target, item_id, quantity, definition
                        )
                    )
                    moved_instance_ids = sorted(
                        {item.instance_id for item in source.instances}
                        - {item.instance_id for item in source_after.instances}
                    )
                    source_result = await self.inventories.replace_one(
                        {**self._scope(source_scope), "state_version": source_version},
                        self._document(source_after),
                        session=session,
                    )
                    target_result = await self.inventories.replace_one(
                        {**self._scope(target_scope), "state_version": target_version},
                        self._document(target_after),
                        session=session,
                    )
                    if source_result.modified_count != 1 or target_result.modified_count != 1:
                        raise InventoryError("inventory_conflict")
                    now = datetime.now(UTC)
                    for scope, operation, related, snapshot in (
                        (source_scope, "transfer_out", target_scope.player_id, source_after),
                        (target_scope, "transfer_in", source_scope.player_id, target_after),
                    ):
                        await self.audit_logs.insert_one(
                            {
                                "audit_id": new_uuid7(),
                                "studio_id": scope.studio_id,
                                "game_id": scope.game_id,
                                "player_id": scope.player_id,
                                "game_profile_id": scope.game_profile_id,
                                "container_id": scope.container_id,
                                "event_type": "inventory.item_history.v1",
                                "operation": operation,
                                "item_id": item_id,
                                "quantity": quantity,
                                "instance_ids": moved_instance_ids,
                                "idempotency_key": idempotency_key,
                                "related_player_id": related,
                                "occurred_at": now,
                            },
                            session=session,
                        )
                        await self.idempotency.insert_one(
                            {
                                **self._scope(scope),
                                "actor_id": actor_id,
                                "idempotency_key": idempotency_key,
                                "fingerprint": fingerprint,
                                "snapshot": self._document(snapshot),
                                "created_at": now,
                                "action_class": "inventory_transfer",
                            },
                            session=session,
                        )
                    return source_after, target_after
        except DuplicateKeyError as error:
            prior_source = await self.idempotency.find_one(source_idem)
            prior_target = await self.idempotency.find_one(target_idem)
            if (
                prior_source is not None
                and prior_target is not None
                and prior_source.get("fingerprint") == fingerprint
                and prior_target.get("fingerprint") == fingerprint
            ):
                return self._snapshot(prior_source["snapshot"]), self._snapshot(
                    prior_target["snapshot"]
                )
            raise InventoryError("inventory_conflict") from error
