"""Deterministic source formatting gate."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "ruff",
            "format",
            "apps",
            "packages",
            "tools",
            "tests",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        return result.returncode
    print("PASS format: deterministic Python formatting applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
