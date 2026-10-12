"""Frozen extension handler registries. Registration order is canonical."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from packages.runtime.src.lengeas_runtime.effects import CORE_EFFECT_NAMES
from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode
from packages.runtime.src.lengeas_runtime.rewards import CORE_REWARD_NAMES

EffectHandler = Callable[[Mapping[str, Any], Mapping[str, Any]], tuple[Mapping[str, Any], ...]]
RewardHandler = Callable[[Mapping[str, Any]], tuple[Mapping[str, Any], ...]]


@dataclass(frozen=True, slots=True)
class HandlerOwner:
    package_id: str
    namespace: str
    digest: str


class HandlerRegistry:
    def __init__(self) -> None:
        self._effects: dict[str, tuple[HandlerOwner, EffectHandler]] = {}
        self._rewards: dict[str, tuple[HandlerOwner, RewardHandler]] = {}
        self._frozen = False

    def register_effect(self, name: str, owner: HandlerOwner, handler: EffectHandler) -> None:
        if self._frozen:
            raise RuntimeErrorCode("registry_frozen")
        if name in self._effects:
            raise RuntimeErrorCode("effect_handler_duplicate")
        self._effects[name] = (owner, handler)

    def register_reward(self, name: str, owner: HandlerOwner, handler: RewardHandler) -> None:
        if self._frozen:
            raise RuntimeErrorCode("registry_frozen")
        if name in self._rewards:
            raise RuntimeErrorCode("reward_handler_duplicate")
        self._rewards[name] = (owner, handler)

    def freeze(self) -> None:
        self._frozen = True

    def effect(
        self, name: str, package_id: str, state: Mapping[str, Any], payload: Mapping[str, Any]
    ) -> tuple[Mapping[str, Any], ...]:
        registered = self._effects.get(name)
        if registered is None:
            raise RuntimeErrorCode("effect_handler_missing")
        owner, handler = registered
        if owner.package_id != package_id:
            raise RuntimeErrorCode("handler_package_mismatch")
        return tuple(handler(state, payload))

    def reward(
        self, name: str, package_id: str, payload: Mapping[str, Any]
    ) -> tuple[Mapping[str, Any], ...]:
        registered = self._rewards.get(name)
        if registered is None:
            raise RuntimeErrorCode("reward_handler_missing")
        owner, handler = registered
        if owner.package_id != package_id:
            raise RuntimeErrorCode("handler_package_mismatch")
        return tuple(handler(payload))

    @property
    def frozen(self) -> bool:
        return self._frozen


def core_registry() -> HandlerRegistry:
    registry = HandlerRegistry()
    owner = HandlerOwner("core", "core", "sha256:core-v1")

    def generic(
        _state: Mapping[str, Any], effect: Mapping[str, Any]
    ) -> tuple[Mapping[str, Any], ...]:
        return (dict(effect),)

    def reward(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
        entries = payload.get("entries", [payload])
        if not isinstance(entries, (list, tuple)):
            raise RuntimeErrorCode("reward_entries_invalid")
        return tuple(dict(entry) for entry in entries)

    for name in CORE_EFFECT_NAMES:
        registry.register_effect(name, owner, generic)
    for name in CORE_REWARD_NAMES:
        registry.register_reward(name, owner, reward)
    registry.freeze()
    return registry
