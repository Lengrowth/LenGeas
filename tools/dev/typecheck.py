"""Strict Python and TypeScript type checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "mypy",
            "--strict",
            "apps/api",
            "apps/workers",
            "packages/runtime",
            "packages/domain",
            "packages/persistence",
            "packages/simulation",
            "tools",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        return result.returncode
    result = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "python",
            "-m",
            "compileall",
            "-q",
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
    node = "pnpm.cmd" if sys.platform == "win32" else "pnpm"
    result = subprocess.run(
        [node, "exec", "tsc", "--noEmit", "--project", "tsconfig.json"], cwd=ROOT, check=False
    )
    if result.returncode:
        return result.returncode
    print("PASS typecheck: strict Python and TypeScript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
