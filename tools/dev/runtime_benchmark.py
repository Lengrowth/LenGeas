"""Record local pure-evaluator timing without importing environment adapters."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/evidence/phase-05/performance/runtime-benchmark.json",
    )
    args = parser.parse_args()
    expression = {
        "operator": "add",
        "args": [
            {
                "operator": "multiply",
                "args": [
                    {"operator": "literal", "value": "1.25"},
                    {"operator": "literal", "value": 40},
                ],
            },
            {"operator": "literal", "value": 7},
        ],
    }
    samples: list[float] = []
    for _ in range(1000):
        started = time.perf_counter_ns()
        result = evaluate_formula(expression, {})
        samples.append((time.perf_counter_ns() - started) / 1_000)
        if result != 57:
            raise SystemExit("runtime benchmark fixture returned an unexpected value")
    report = {
        "status": "passed" if max(samples) <= 50_000 else "failed",
        "benchmark": "1000 evaluations of bounded add/multiply formula",
        "budget_micros_per_evaluation": 50_000,
        "evaluations": len(samples),
        "p50_micros": statistics.median(samples),
        "p95_micros": sorted(samples)[int(len(samples) * 0.95) - 1],
        "max_micros": max(samples),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "limitations": (
            "Local developer CPU; reference CPU threshold is not established on this host."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
