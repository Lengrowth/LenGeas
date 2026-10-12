"""Immutable, fully pinned inputs for deterministic evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode


@dataclass(frozen=True, slots=True)
class ExecutionBudgets:
    condition_nodes: int = 256
    formula_operations: int = 512
    effects: int = 128
    events: int = 64
    state_patch_bytes: int = 256 * 1024
    execution_micros: int = 50_000

    def __post_init__(self) -> None:
        if (
            min(
                self.condition_nodes,
                self.formula_operations,
                self.effects,
                self.events,
                self.state_patch_bytes,
                self.execution_micros,
            )
            < 0
        ):
            raise RuntimeErrorCode("budget_invalid")


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    engine_version: str
    definition_digest: str
    package_digests: tuple[tuple[str, str], ...]
    state_version: int
    action_id: str
    logical_time: datetime
    seed: int
    experiment_assignments: tuple[tuple[str, str], ...]
    locale: str
    actor_id: str
    studio_id: str
    game_id: str
    player_id: str
    readable_namespaces: frozenset[str]
    writable_namespaces: frozenset[str]
    budgets: ExecutionBudgets = ExecutionBudgets()
    rng_algorithm: str = "pcg64-v1"

    def __post_init__(self) -> None:
        if self.state_version < 0 or not 0 <= self.seed < 2**128:
            raise RuntimeErrorCode("execution_context_invalid")
        if (
            not self.engine_version
            or not self.definition_digest
            or any(not package or not digest for package, digest in self.package_digests)
        ):
            raise RuntimeErrorCode("execution_inputs_unpinned")
        if self.logical_time.tzinfo is None or self.logical_time.utcoffset() is None:
            raise RuntimeErrorCode("logical_time_must_be_aware")
        normalized = self.logical_time.astimezone(UTC)
        object.__setattr__(self, "logical_time", normalized)
        object.__setattr__(self, "package_digests", tuple(sorted(self.package_digests)))
        object.__setattr__(
            self, "experiment_assignments", tuple(sorted(self.experiment_assignments))
        )
        object.__setattr__(self, "readable_namespaces", frozenset(self.readable_namespaces))
        object.__setattr__(self, "writable_namespaces", frozenset(self.writable_namespaces))

    @property
    def execution_tuple(self) -> tuple[object, ...]:
        return (
            self.engine_version,
            self.definition_digest,
            self.package_digests,
            self.state_version,
            self.action_id,
            self.logical_time.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            self.seed,
        )
