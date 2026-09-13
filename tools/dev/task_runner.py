"""Cross-platform entrypoint for the LenGeas repository task contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str], *, check: bool = True) -> int:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if check and completed.returncode:
        raise SystemExit(completed.returncode)
    return completed.returncode


def required_paths() -> list[Path]:
    return [
        ROOT / "apps",
        ROOT / "packages",
        ROOT / "mechanics",
        ROOT / "infrastructure",
        ROOT / "tests",
        ROOT / "Taskfile.yml",
        ROOT / "pyproject.toml",
        ROOT / "pnpm-workspace.yaml",
    ]


def bootstrap() -> None:
    missing = [str(path.relative_to(ROOT)) for path in required_paths() if not path.exists()]
    if missing:
        raise SystemExit(f"bootstrap failed; missing required paths: {', '.join(missing)}")
    print("PASS bootstrap: monorepo structure and root contracts are present")


def tool_script(name: str, *args: str) -> int:
    script = ROOT / "tools" / "dev" / f"{name}.py"
    if not script.exists():
        raise SystemExit(f"missing development tool: {script.relative_to(ROOT)}")
    return run([sys.executable, str(script), *args])


def test_suite(name: str) -> int:
    return tool_script("test_harness", name)


def verify() -> None:
    for name in ("format", "lint", "typecheck"):
        tool_script(name)
    for suite in ("unit", "property", "contract", "integration", "e2e", "security", "performance", "determinism", "disaster-recovery"):
        test_suite(suite)
    print("PASS verify: required local merge-gate checks completed")


def evidence(phase: str) -> int:
    return tool_script("evidence", phase)


def phase_gate(phase: str) -> int:
    return tool_script("phase_gate", phase)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args()
    command = parsed.command
    if command == "bootstrap":
        bootstrap()
        return 0
    if command == "generate":
        return tool_script("generate")
    if command in {"format", "lint", "typecheck"}:
        return tool_script(command)
    if command == "test":
        if len(parsed.args) != 1:
            raise SystemExit("usage: task_runner.py test <suite>")
        return test_suite(parsed.args[0])
    if command == "verify":
        verify()
        return 0
    if command == "evidence":
        return evidence(parsed.args[0] if parsed.args else "01")
    if command == "phase-gate":
        return phase_gate(parsed.args[0] if parsed.args else "01")
    if command in {"local-up", "local-smoke", "local-down"}:
        return tool_script("local", command.removeprefix("local-"))
    raise SystemExit(f"unknown repository command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
