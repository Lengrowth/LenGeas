"""Bounded inventories for stackable items and uniquely identified instances."""

from __future__ import annotations

import copy
import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from packages.domain.ids import new_uuid7


class InventoryError(ValueError):
    """An inventory operation violated capacity, ownership, or version rules."""


MAX_ITEM_ATTRIBUTE_BYTES = 64 * 1024


def validate_item_attributes(attributes: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(attributes or {})

    def validate_keys(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if not isinstance(key, str) or not key or key.startswith("$") or "." in key:
                    raise InventoryError("invalid_item_attribute_path")
                validate_keys(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                validate_keys(nested)

    validate_keys(value)
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError) as error:
        raise InventoryError("item_attributes_not_canonical_json") from error
    if len(encoded) > MAX_ITEM_ATTRIBUTE_BYTES:
        raise InventoryError("item_attributes_too_large")
    return value


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    item_id: str
    stackable: bool
    max_stack: int = 1
    transferable: bool = False
    equipment_slots: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if (
            not self.item_id
            or isinstance(self.max_stack, bool)
            or not isinstance(self.max_stack, int)
            or self.max_stack < 1
        ):
            raise InventoryError("invalid_item_definition")
        if not self.stackable and self.max_stack != 1:
            raise InventoryError("unique_item_stack_limit")


@dataclass(frozen=True, slots=True)
class ItemStack:
    stack_id: str
    item_id: str
    quantity: int
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ItemInstance:
    instance_id: str
    item_id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InventoryScope:
    studio_id: str
    game_id: str
    player_id: str
    game_profile_id: str
    container_id: str

    def __post_init__(self) -> None:
        if not all(
            (self.studio_id, self.game_id, self.player_id, self.game_profile_id, self.container_id)
        ):
            raise InventoryError("inventory_scope_required")


@dataclass(frozen=True, slots=True)
class ItemHistoryRecord:
    history_id: str
    scope: InventoryScope
    operation: str
    item_id: str
    quantity: int
    idempotency_key: str
    occurred_at: datetime
    related_player_id: str | None = None
    instance_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InventorySnapshot:
    scope: InventoryScope
    state_version: int
    capacity_slots: int
    stacks: tuple[ItemStack, ...]
    instances: tuple[ItemInstance, ...]
    equipment: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class InventoryRewardGrant:
    scope: InventoryScope
    definition: ItemDefinition
    quantity: int
    expected_version: int
    attributes: Mapping[str, Any] = field(default_factory=dict)


def plan_inventory_grant(
    current: InventorySnapshot,
    definition: ItemDefinition,
    quantity: int,
    attributes: Mapping[str, Any] | None = None,
) -> InventorySnapshot:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise InventoryError("invalid_item_quantity")
    stacks, instances = list(current.stacks), list(current.instances)
    attrs = dict(attributes or {})
    remaining = quantity
    if definition.stackable:
        for index, stack in enumerate(stacks):
            if stack.item_id != definition.item_id or dict(stack.attributes) != attrs:
                continue
            added = min(max(0, definition.max_stack - stack.quantity), remaining)
            if added:
                stacks[index] = ItemStack(
                    stack.stack_id, stack.item_id, stack.quantity + added, stack.attributes
                )
                remaining -= added
            if not remaining:
                break
    new_slots = (
        (remaining + definition.max_stack - 1) // definition.max_stack
        if definition.stackable
        else remaining
    )
    if len(stacks) + len(instances) + new_slots > current.capacity_slots:
        raise InventoryError("inventory_capacity_exceeded")
    while remaining:
        if definition.stackable:
            amount = min(remaining, definition.max_stack)
            stacks.append(ItemStack(new_uuid7(), definition.item_id, amount, attrs))
            remaining -= amount
        else:
            instances.append(ItemInstance(new_uuid7(), definition.item_id, attrs))
            remaining -= 1
    return InventorySnapshot(
        current.scope,
        current.state_version + 1,
        current.capacity_slots,
        tuple(stacks),
        tuple(instances),
        dict(current.equipment),
    )


def plan_inventory_consume(
    current: InventorySnapshot, item_id: str, quantity: int
) -> InventorySnapshot:
    if quantity < 1:
        raise InventoryError("invalid_consumption")
    stacks, instances = list(current.stacks), list(current.instances)
    available = sum(stack.quantity for stack in stacks if stack.item_id == item_id)
    available += sum(instance.item_id == item_id for instance in instances)
    if available < quantity:
        raise InventoryError("insufficient_items")
    remaining = quantity
    kept_stacks: list[ItemStack] = []
    for stack in stacks:
        if stack.item_id != item_id or not remaining:
            kept_stacks.append(stack)
            continue
        removed = min(stack.quantity, remaining)
        remaining -= removed
        if removed < stack.quantity:
            kept_stacks.append(
                ItemStack(stack.stack_id, stack.item_id, stack.quantity - removed, stack.attributes)
            )
    kept_instances: list[ItemInstance] = []
    for instance in instances:
        if instance.item_id == item_id and remaining:
            remaining -= 1
        else:
            kept_instances.append(instance)
    equipment = {
        slot: instance_id
        for slot, instance_id in current.equipment.items()
        if any(item.instance_id == instance_id for item in kept_instances)
    }
    return InventorySnapshot(
        current.scope,
        current.state_version + 1,
        current.capacity_slots,
        tuple(kept_stacks),
        tuple(kept_instances),
        equipment,
    )


def plan_inventory_equip(
    current: InventorySnapshot, instance_id: str, slot: str, definition: ItemDefinition
) -> InventorySnapshot:
    if slot not in definition.equipment_slots:
        raise InventoryError("equipment_slot_not_allowed")
    if not any(
        item.instance_id == instance_id and item.item_id == definition.item_id
        for item in current.instances
    ):
        raise InventoryError("item_instance_not_owned")
    equipment = {
        existing_slot: existing_instance
        for existing_slot, existing_instance in current.equipment.items()
        if existing_instance != instance_id
    }
    equipment[slot] = instance_id
    return InventorySnapshot(
        current.scope,
        current.state_version + 1,
        current.capacity_slots,
        current.stacks,
        current.instances,
        equipment,
    )


class InMemoryInventoryRepository:
    """Atomic test adapter. Production operations use MongoDB transactions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._inventories: dict[InventoryScope, InventorySnapshot] = {}
        self._history: list[ItemHistoryRecord] = []
        self._idempotency: dict[tuple[InventoryScope, str], tuple[str, InventorySnapshot]] = {}

    def create(self, scope: InventoryScope, capacity_slots: int) -> InventorySnapshot:
        if capacity_slots < 0:
            raise InventoryError("invalid_inventory_capacity")
        with self._lock:
            if scope in self._inventories:
                raise InventoryError("inventory_exists")
            value = InventorySnapshot(scope, 0, capacity_slots, (), (), {})
            self._inventories[scope] = value
            return value

    def read(self, scope: InventoryScope) -> InventorySnapshot | None:
        with self._lock:
            return copy.deepcopy(self._inventories.get(scope))

    def history(self, scope: InventoryScope) -> tuple[ItemHistoryRecord, ...]:
        with self._lock:
            return tuple(record for record in self._history if record.scope == scope)

    def grant(
        self,
        scope: InventoryScope,
        definition: ItemDefinition,
        quantity: int,
        *,
        expected_version: int,
        idempotency_key: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> InventorySnapshot:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise InventoryError("invalid_item_quantity")
        if not idempotency_key:
            raise InventoryError("idempotency_key_required")
        fingerprint = f"grant:{definition.item_id}:{quantity}:{dict(attributes or {})}"
        with self._lock:
            replay = self._idempotency.get((scope, idempotency_key))
            if replay is not None:
                if replay[0] != fingerprint:
                    raise InventoryError("idempotency_conflict")
                return copy.deepcopy(replay[1])
            current = self._inventories.get(scope)
            if current is None:
                raise InventoryError("inventory_not_found")
            if current.state_version != expected_version:
                raise InventoryError("inventory_conflict")
            stacks = list(current.stacks)
            instances = list(current.instances)
            remaining = quantity
            if definition.stackable:
                for index, stack in enumerate(stacks):
                    if stack.item_id != definition.item_id or dict(stack.attributes) != dict(
                        attributes or {}
                    ):
                        continue
                    room = definition.max_stack - stack.quantity
                    if room > 0:
                        added = min(room, remaining)
                        stacks[index] = ItemStack(
                            stack.stack_id, stack.item_id, stack.quantity + added, stack.attributes
                        )
                        remaining -= added
                        if remaining == 0:
                            break
            used = len(stacks) + len(instances)
            new_slots = (remaining + definition.max_stack - 1) // definition.max_stack
            if used + new_slots > current.capacity_slots:
                raise InventoryError("inventory_capacity_exceeded")
            while remaining:
                if definition.stackable:
                    amount = min(remaining, definition.max_stack)
                    stacks.append(
                        ItemStack(new_uuid7(), definition.item_id, amount, dict(attributes or {}))
                    )
                    remaining -= amount
                else:
                    instances.append(
                        ItemInstance(new_uuid7(), definition.item_id, dict(attributes or {}))
                    )
                    remaining -= 1
            updated = InventorySnapshot(
                scope,
                current.state_version + 1,
                current.capacity_slots,
                tuple(stacks),
                tuple(instances),
                dict(current.equipment),
            )
            self._commit(
                scope,
                current,
                updated,
                "grant",
                definition.item_id,
                quantity,
                idempotency_key,
                fingerprint,
            )
            return copy.deepcopy(updated)

    def consume(
        self,
        scope: InventoryScope,
        item_id: str,
        quantity: int,
        *,
        expected_version: int,
        idempotency_key: str,
    ) -> InventorySnapshot:
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity < 1
            or not idempotency_key
        ):
            raise InventoryError("invalid_consumption")
        fingerprint = f"consume:{item_id}:{quantity}"
        with self._lock:
            replay = self._idempotency.get((scope, idempotency_key))
            if replay is not None:
                if replay[0] != fingerprint:
                    raise InventoryError("idempotency_conflict")
                return copy.deepcopy(replay[1])
            current = self._current(scope, expected_version)
            stacks = list(current.stacks)
            instances = list(current.instances)
            available = sum(stack.quantity for stack in stacks if stack.item_id == item_id)
            available += sum(instance.item_id == item_id for instance in instances)
            if available < quantity:
                raise InventoryError("insufficient_items")
            remaining = quantity
            kept_stacks: list[ItemStack] = []
            for stack in stacks:
                if stack.item_id != item_id or remaining == 0:
                    kept_stacks.append(stack)
                    continue
                used = min(stack.quantity, remaining)
                remaining -= used
                if stack.quantity > used:
                    kept_stacks.append(
                        ItemStack(
                            stack.stack_id, stack.item_id, stack.quantity - used, stack.attributes
                        )
                    )
            kept_instances: list[ItemInstance] = []
            for instance in instances:
                if instance.item_id == item_id and remaining > 0:
                    remaining -= 1
                else:
                    kept_instances.append(instance)
            equipment = {
                slot: instance_id
                for slot, instance_id in current.equipment.items()
                if any(item.instance_id == instance_id for item in kept_instances)
            }
            updated = InventorySnapshot(
                scope,
                current.state_version + 1,
                current.capacity_slots,
                tuple(kept_stacks),
                tuple(kept_instances),
                equipment,
            )
            self._commit(
                scope, current, updated, "consume", item_id, quantity, idempotency_key, fingerprint
            )
            return copy.deepcopy(updated)

    def equip(
        self,
        scope: InventoryScope,
        instance_id: str,
        slot: str,
        definition: ItemDefinition,
        *,
        expected_version: int,
        idempotency_key: str,
    ) -> InventorySnapshot:
        if not idempotency_key:
            raise InventoryError("idempotency_key_required")
        fingerprint = f"equip:{instance_id}:{slot}:{definition.item_id}"
        with self._lock:
            replay = self._idempotency.get((scope, idempotency_key))
            if replay is not None:
                if replay[0] != fingerprint:
                    raise InventoryError("idempotency_conflict")
                return copy.deepcopy(replay[1])
            current = self._current(scope, expected_version)
            updated = plan_inventory_equip(current, instance_id, slot, definition)
            self._commit(
                scope,
                current,
                updated,
                "equip",
                definition.item_id,
                1,
                idempotency_key,
                fingerprint,
            )
            return copy.deepcopy(updated)

    def transfer(
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
    ) -> tuple[InventorySnapshot, InventorySnapshot]:
        if not definition.transferable:
            raise InventoryError("item_transfer_denied")
        if (
            source_scope.studio_id != target_scope.studio_id
            or source_scope.game_id != target_scope.game_id
        ):
            raise InventoryError("cross_game_transfer_denied")
        if (
            source_scope.player_id == target_scope.player_id
            or isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity < 1
        ):
            raise InventoryError("invalid_transfer")
        if not idempotency_key:
            raise InventoryError("idempotency_key_required")
        with self._lock:
            fingerprint = (
                f"transfer:{target_scope.player_id}:{item_id}:{quantity}:"
                f"{definition.stackable}:{definition.max_stack}:{definition.transferable}"
            )
            prior_source = self._idempotency.get((source_scope, idempotency_key))
            prior_target = self._idempotency.get((target_scope, idempotency_key))
            if prior_source is not None or prior_target is not None:
                if (
                    prior_source is None
                    or prior_target is None
                    or prior_source[0] != fingerprint
                    or prior_target[0] != fingerprint
                ):
                    raise InventoryError("idempotency_conflict")
                return copy.deepcopy(prior_source[1]), copy.deepcopy(prior_target[1])
            source = self._current(source_scope, source_version)
            target = self._current(target_scope, target_version)
            source_after, target_after = self.plan_transfer_snapshots(
                source, target, item_id, quantity, definition
            )
            self._inventories[source_scope] = source_after
            self._inventories[target_scope] = target_after
            now = datetime.now(UTC)
            source_ids = {instance.instance_id for instance in source.instances}
            source_after_ids = {instance.instance_id for instance in source_after.instances}
            moved_instance_ids = tuple(sorted(source_ids - source_after_ids))
            self._history.extend(
                (
                    ItemHistoryRecord(
                        new_uuid7(),
                        source_scope,
                        "transfer_out",
                        item_id,
                        quantity,
                        idempotency_key,
                        now,
                        target_scope.player_id,
                        moved_instance_ids,
                    ),
                    ItemHistoryRecord(
                        new_uuid7(),
                        target_scope,
                        "transfer_in",
                        item_id,
                        quantity,
                        idempotency_key,
                        now,
                        source_scope.player_id,
                        moved_instance_ids,
                    ),
                )
            )
            self._idempotency[(source_scope, idempotency_key)] = (fingerprint, source_after)
            self._idempotency[(target_scope, idempotency_key)] = (fingerprint, target_after)
            return copy.deepcopy(source_after), copy.deepcopy(target_after)

    @classmethod
    def plan_transfer_snapshots(
        cls,
        source: InventorySnapshot,
        target: InventorySnapshot,
        item_id: str,
        quantity: int,
        definition: ItemDefinition,
    ) -> tuple[InventorySnapshot, InventorySnapshot]:
        if not definition.transferable:
            raise InventoryError("item_transfer_denied")
        if (
            source.scope.studio_id != target.scope.studio_id
            or source.scope.game_id != target.scope.game_id
        ):
            raise InventoryError("cross_game_transfer_denied")
        if source.scope.player_id == target.scope.player_id or quantity < 1:
            raise InventoryError("invalid_transfer")
        if definition.stackable:
            return cls._simulate_stack_transfer(source, target, item_id, quantity, definition)
        moving = [item for item in source.instances if item.item_id == item_id][:quantity]
        if len(moving) != quantity:
            raise InventoryError("insufficient_items")
        if len(target.stacks) + len(target.instances) + quantity > target.capacity_slots:
            raise InventoryError("inventory_capacity_exceeded")
        moving_ids = {item.instance_id for item in moving}
        source_instances = tuple(
            item for item in source.instances if item.instance_id not in moving_ids
        )
        source_equipment = {
            slot: instance_id
            for slot, instance_id in source.equipment.items()
            if instance_id not in moving_ids
        }
        source_after = InventorySnapshot(
            source.scope,
            source.state_version + 1,
            source.capacity_slots,
            source.stacks,
            source_instances,
            source_equipment,
        )
        target_after = InventorySnapshot(
            target.scope,
            target.state_version + 1,
            target.capacity_slots,
            target.stacks,
            (*target.instances, *moving),
            dict(target.equipment),
        )
        return source_after, target_after

    def _current(self, scope: InventoryScope, expected_version: int) -> InventorySnapshot:
        current = self._inventories.get(scope)
        if current is None:
            raise InventoryError("inventory_not_found")
        if current.state_version != expected_version:
            raise InventoryError("inventory_conflict")
        return current

    def _commit(
        self,
        scope: InventoryScope,
        current: InventorySnapshot,
        updated: InventorySnapshot,
        operation: str,
        item_id: str,
        quantity: int,
        idempotency_key: str,
        fingerprint: str,
    ) -> None:
        self._inventories[scope] = updated
        self._idempotency[(scope, idempotency_key)] = (fingerprint, updated)
        prior_instance_ids = {item.instance_id for item in current.instances}
        next_instance_ids = {item.instance_id for item in updated.instances}
        self._history.append(
            ItemHistoryRecord(
                new_uuid7(),
                scope,
                operation,
                item_id,
                quantity,
                idempotency_key,
                datetime.now(UTC),
                instance_ids=tuple(
                    sorted(prior_instance_ids.symmetric_difference(next_instance_ids))
                ),
            )
        )

    @staticmethod
    def _simulate_consume(
        current: InventorySnapshot, item_id: str, quantity: int
    ) -> InventorySnapshot:
        stacks = list(current.stacks)
        instances = list(current.instances)
        available = sum(stack.quantity for stack in stacks if stack.item_id == item_id)
        available += sum(item.item_id == item_id for item in instances)
        if available < quantity:
            raise InventoryError("insufficient_items")
        remaining = quantity
        kept: list[ItemStack] = []
        for stack in stacks:
            if stack.item_id != item_id or remaining == 0:
                kept.append(stack)
            else:
                used = min(stack.quantity, remaining)
                remaining -= used
                if stack.quantity > used:
                    kept.append(
                        ItemStack(
                            stack.stack_id, stack.item_id, stack.quantity - used, stack.attributes
                        )
                    )
        kept_instances: list[ItemInstance] = []
        for item in instances:
            if item.item_id == item_id and remaining:
                remaining -= 1
            else:
                kept_instances.append(item)
        equipment = {
            slot: iid
            for slot, iid in current.equipment.items()
            if any(item.instance_id == iid for item in kept_instances)
        }
        return InventorySnapshot(
            current.scope,
            current.state_version + 1,
            current.capacity_slots,
            tuple(kept),
            tuple(kept_instances),
            equipment,
        )

    @staticmethod
    def _simulate_grant(
        current: InventorySnapshot, definition: ItemDefinition, quantity: int
    ) -> InventorySnapshot:
        stacks = list(current.stacks)
        instances = list(current.instances)
        remaining = quantity
        if definition.stackable:
            for index, stack in enumerate(stacks):
                if stack.item_id != definition.item_id:
                    continue
                room = definition.max_stack - stack.quantity
                added = min(max(room, 0), remaining)
                if added:
                    stacks[index] = ItemStack(
                        stack.stack_id, stack.item_id, stack.quantity + added, stack.attributes
                    )
                    remaining -= added
                if not remaining:
                    break
        if (
            len(stacks)
            + len(instances)
            + (remaining + definition.max_stack - 1) // definition.max_stack
            > current.capacity_slots
        ):
            raise InventoryError("inventory_capacity_exceeded")
        while remaining:
            if definition.stackable:
                amount = min(remaining, definition.max_stack)
                stacks.append(ItemStack(new_uuid7(), definition.item_id, amount))
                remaining -= amount
            else:
                instances.append(ItemInstance(new_uuid7(), definition.item_id))
                remaining -= 1
        return InventorySnapshot(
            current.scope,
            current.state_version + 1,
            current.capacity_slots,
            tuple(stacks),
            tuple(instances),
            dict(current.equipment),
        )

    @staticmethod
    def _simulate_stack_transfer(
        source: InventorySnapshot,
        target: InventorySnapshot,
        item_id: str,
        quantity: int,
        definition: ItemDefinition,
    ) -> tuple[InventorySnapshot, InventorySnapshot]:
        available = sum(stack.quantity for stack in source.stacks if stack.item_id == item_id)
        if available < quantity:
            raise InventoryError("insufficient_items")
        remaining = quantity
        source_stacks: list[ItemStack] = []
        incoming: list[tuple[int, Mapping[str, Any]]] = []
        for stack in source.stacks:
            if stack.item_id != item_id or remaining == 0:
                source_stacks.append(stack)
                continue
            moved = min(stack.quantity, remaining)
            remaining -= moved
            incoming.append((moved, stack.attributes))
            if stack.quantity > moved:
                source_stacks.append(
                    ItemStack(
                        stack.stack_id, stack.item_id, stack.quantity - moved, stack.attributes
                    )
                )
        target_stacks = list(target.stacks)
        for amount, attributes in incoming:
            compatible = [
                stack
                for stack in target_stacks
                if stack.item_id == item_id and dict(stack.attributes) == dict(attributes)
            ]
            for stack in compatible:
                moved = min(definition.max_stack - stack.quantity, amount)
                if moved:
                    target_stacks[target_stacks.index(stack)] = ItemStack(
                        stack.stack_id, stack.item_id, stack.quantity + moved, stack.attributes
                    )
                    amount -= moved
                if amount == 0:
                    break
            while amount:
                moved = min(definition.max_stack, amount)
                target_stacks.append(ItemStack(new_uuid7(), item_id, moved, dict(attributes)))
                amount -= moved
        occupied = len(target_stacks) + len(target.instances)
        if occupied > target.capacity_slots:
            raise InventoryError("inventory_capacity_exceeded")
        return (
            InventorySnapshot(
                source.scope,
                source.state_version + 1,
                source.capacity_slots,
                tuple(source_stacks),
                source.instances,
                dict(source.equipment),
            ),
            InventorySnapshot(
                target.scope,
                target.state_version + 1,
                target.capacity_slots,
                tuple(target_stacks),
                target.instances,
                dict(target.equipment),
            ),
        )
