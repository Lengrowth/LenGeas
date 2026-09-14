"""Cross-platform entrypoint for the LenGeas repository task contract."""

from __future__ import annotations

import argparse
import shutil
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
    if shutil.which("uv") is None:
        raise SystemExit("bootstrap failed; uv 0.11.29 is required")
    pnpm = "pnpm.cmd" if sys.platform == "win32" else "pnpm"
    if shutil.which(pnpm) is None:
        raise SystemExit("bootstrap failed; pnpm 11.20.0 is required")
    run(["uv", "sync", "--frozen", "--python", "3.13.5"])
    run([pnpm, "install", "--frozen-lockfile", "--ignore-scripts"])
    print("PASS bootstrap: pinned Python and JavaScript environments installed")


def tool_script(name: str, *args: str, check: bool = True) -> int:
    script = ROOT / "tools" / "dev" / f"{name}.py"
    if not script.exists():
        raise SystemExit(f"missing development tool: {script.relative_to(ROOT)}")
    return run([sys.executable, str(script), *args], check=check)


def test_suite(name: str, *selectors: str, check: bool = True) -> int:
    return tool_script("test_harness", name, *selectors, check=check)


def verify() -> None:
    failures: list[str] = []
    for name in ("format", "lint", "typecheck"):
        if tool_script(name, check=False):
            failures.append(name)
    for suite in (
        "unit",
        "property",
        "contract",
        "integration",
        "e2e",
        "security",
        "performance",
        "determinism",
        "disaster-recovery",
    ):
        if test_suite(suite, check=False):
            failures.append(f"test:{suite}")
    for check_name in (
        "workflow-policy",
        "terraform-policy",
        "docs-links",
        "schema",
        "openapi",
        "license-policy",
        "phase02-policy",
    ):
        if tool_script("ci_checks", check_name, check=False):
            failures.append(f"ci:{check_name}")
    if failures:
        print("FAIL verify: " + ", ".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("PASS verify: required local merge-gate checks completed")


def evidence(phase: str, *, regenerate: bool = False) -> int:
    arguments = [phase]
    if regenerate:
        arguments.append("--regenerate")
    return tool_script("evidence", *arguments)


def phase_gate(phase: str) -> int:
    return tool_script("phase_gate", phase)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--regenerate", action="store_true")
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
        if len(parsed.args) not in {1, 2}:
            raise SystemExit("usage: task_runner.py test <suite> [selector]")
        return test_suite(parsed.args[0], *(parsed.args[1:]))
    if command == "verify":
        verify()
        return 0
    if command == "evidence":
        phase = parsed.args[0] if parsed.args and not parsed.args[0].startswith("-") else "01"
        return evidence(phase, regenerate=parsed.regenerate)
    if command == "phase-gate":
        return phase_gate(parsed.args[0] if parsed.args else "01")
    if command in {"local-up", "local-smoke", "local-down"}:
        return tool_script("local", command.removeprefix("local-"))
    raise SystemExit(f"unknown repository command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
