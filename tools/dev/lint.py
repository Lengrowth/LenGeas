"""Repository lint and policy checks."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = re.compile(r"(^|[\s'\"])(latest|\^|~)(?=($|[\s'\"]|:))", re.IGNORECASE)
SECRET = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]+['\"]")


def _text_files() -> list[Path]:
    roots = [
        ROOT / ".tool-versions",
        ROOT / ".env.example",
        ROOT / "Taskfile.yml",
        ROOT / "package.json",
        ROOT / "pnpm-workspace.yaml",
        ROOT / "pnpm-lock.yaml",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "compose.yaml",
        ROOT / ".github",
        ROOT / "infrastructure",
        ROOT / "apps",
        ROOT / "packages",
        ROOT / "mechanics",
    ]
    files: set[Path] = set()
    for path in roots:
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(
                item
                for item in path.rglob("*")
                if item.is_file()
                and ".git" not in item.parts
                and "node_modules" not in item.parts
                and ".venv" not in item.parts
                and ".terraform" not in item.parts
                and "__pycache__" not in item.parts
            )
    return sorted(files)


def main() -> int:
    violations: list[str] = []
    for path in _text_files():
        if path.suffix.lower() not in {
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".md",
            ".py",
            ".ts",
            ".tsx",
            ".tf",
            ".tfvars",
        } and path.name not in {"Taskfile.yml", ".tool-versions"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if FORBIDDEN.search(text):
            violations.append(f"mutable dependency tag or range in {path.relative_to(ROOT)}")
        if SECRET.search(text) and path.name != ".env.example":
            violations.append(f"credential-like literal in {path.relative_to(ROOT)}")
        if "TODO" in text or "FIXME" in text:
            violations.append(f"unresolved work marker in {path.relative_to(ROOT)}")
    for path in sorted(ROOT.rglob("*.json")):
        if (
            ".git" in path.parts
            or "node_modules" in path.parts
            or ".venv" in path.parts
            or ".terraform" in path.parts
        ):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    result = subprocess.run(
        ["uv", "run", "--frozen", "ruff", "check", "apps", "packages", "tools", "tests"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        return result.returncode
    if violations:
        print("\n".join(f"FAIL {item}" for item in violations), file=sys.stderr)
        return 1
    print("PASS lint: Python, JSON, and repository policy checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
