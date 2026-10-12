"""Generate deterministic 1,000-seed replay evidence on the current architecture."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.runtime.src.lengeas_runtime.actions import plan_action  # noqa: E402
from packages.runtime.src.lengeas_runtime.context import ExecutionContext  # noqa: E402
from packages.runtime.src.lengeas_runtime.registry import core_registry  # noqa: E402
from packages.runtime.src.lengeas_runtime.rng import PCG64  # noqa: E402
from packages.runtime.src.lengeas_runtime.serialization import canonical_bytes  # noqa: E402
from packages.runtime.src.lengeas_runtime.state_paths import (  # noqa: E402
    StatePath,
    StatePathRegistry,
)


def replay(seed: int) -> bytes:
    generator = PCG64.from_seed(seed)
    payload = {"amount": generator.randbelow(1000)}
    logical_time = datetime(2030, 1, 1, tzinfo=UTC)
    context = ExecutionContext(
        "1.0.0",
        "sha256:definition",
        (("core", "sha256:core"),),
        0,
        "act_replay",
        logical_time,
        seed,
        (),
        "en",
        "actor_fixture",
        "studio_fixture",
        "game_fixture",
        "player_fixture",
        frozenset({"player"}),
        frozenset({"player"}),
    )
    paths = StatePathRegistry()
    paths.register(
        StatePath("player.score", "player", "core", int, frozenset({"core"}), frozenset({"core"}))
    )
    paths.freeze()
    state = {"player": {"score": 0}}
    action = {
        "id": "act_replay",
        "input_schema": {
            "type": "object",
            "required": ["amount"],
            "additionalProperties": False,
            "properties": {"amount": {"type": "integer", "minimum": 0, "maximum": 999}},
        },
        "conditions": [{"operator": "gte", "left": {"path": "player.score"}, "right": 0}],
        "effects": [
            {
                "operation": "increment",
                "path": "player.score",
                "value": {
                    "expression": {"operator": "variable", "name": "amount"},
                    "variables": ["amount"],
                },
            }
        ],
        "emitted_events": ["runtime.action.replayed.v1"],
    }
    plan = plan_action(
        action,
        payload,
        state,
        context=context,
        path_registry=paths,
        handler_registry=core_registry(),
    )
    if not plan.allowed:
        raise SystemExit("replay fixture action was denied")
    next_state = {"player": {"score": state["player"]["score"] + plan.effects[0].value}}
    return canonical_bytes(
        {
            "context": context.execution_tuple,
            "input_digest": plan.input_digest,
            "allowed": plan.allowed,
            "explanation": plan.explanation.as_dict(),
            "operations": [
                {
                    "kind": op.kind,
                    "package": op.package_id,
                    "path": op.path,
                    "value": op.value,
                    "ordinal": op.ordinal,
                }
                for op in plan.operations
            ],
            "events": [
                {
                    "ordinal": event.ordinal,
                    "type": event.event_type,
                    "occurred_at": event.occurred_at,
                    "payload": event.payload,
                }
                for event in plan.events
            ],
            "state": next_state,
            "state_digest": hashlib.sha256(canonical_bytes(next_state)).hexdigest(),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/evidence/phase-05/performance/replay-local.json"
    )
    args = parser.parse_args()
    records = []
    for seed in range(1000):
        first, second = replay(seed), replay(seed)
        if first != second:
            raise SystemExit(f"replay mismatch at seed {seed}")
        records.append(hashlib.sha256(first).hexdigest())
    report = {
        "status": "passed",
        "seeds": 1000,
        "algorithm": "pcg64-v1",
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "aggregate_sha256": hashlib.sha256("".join(records).encode()).hexdigest(),
        "seed_sha256": records,
        "signed": False,
        "signature_note": (
            "No owner-managed signing key is configured for Phase 05 replay evidence."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "seed_sha256"}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
