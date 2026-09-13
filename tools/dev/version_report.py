"""Emit a deterministic report of declared and observed repository tool versions."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXACT_NPM = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
EXACT_PYTHON = re.compile(r"^[A-Za-z0-9_.-]+==\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tool_versions() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".tool-versions").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, version = line.split(maxsplit=1)
            values[name] = version
    return values


def command_result(command: list[str]) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"command": command, "status": "unavailable", "output": None}
    try:
        completed = subprocess.run(  # noqa: S603 - commands are static and repository-owned
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return {
            "command": command,
            "status": "unavailable",
            "output": f"{type(error).__name__}: {error}",
        }
    output = (completed.stdout or completed.stderr).strip()
    return {
        "command": command,
        "status": "available" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "output": output or None,
    }


def observed_commands() -> dict[str, list[str]]:
    if platform.system() == "Windows":
        python_313 = ["py", "-3.13", "--version"]
        pnpm = ["pnpm.cmd", "--version"]
    else:
        python_313 = ["python3.13", "--version"]
        pnpm = ["pnpm", "--version"]
    return {
        "python_default": ["python", "--version"],
        "python_3_13": python_313,
        "nodejs": ["node", "--version"],
        "pnpm": pnpm,
        "uv": ["uv", "--version"],
        "terraform": ["terraform", "version"],
        "task": ["task", "--version"],
        "docker": ["docker", "version", "--format", "{{.Server.Version}}"],
    }


def declared_dependencies() -> dict[str, Any]:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    py_pins = re.findall(r'^\s*"([A-Za-z0-9_.-]+==[^"\n]+)",?$', pyproject, re.MULTILINE)
    npm_pins: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        npm_pins.update(package.get(section, {}))
    requires_python = re.search(r'^requires-python\s*=\s*"([^"]+)"$', pyproject, re.MULTILINE)
    if requires_python is None:
        raise ValueError("pyproject.toml is missing requires-python")
    return {
        "python": {
            "requires_python": requires_python.group(1),
            "exact_requirements": sorted(py_pins),
            "all_exact": all(EXACT_PYTHON.fullmatch(pin) for pin in py_pins),
        },
        "npm": {
            "package_manager": package["packageManager"],
            "engines": package.get("engines", {}),
            "exact_dependencies": dict(sorted(npm_pins.items())),
            "all_exact": all(EXACT_NPM.fullmatch(value) for value in npm_pins.values()),
        },
    }


def main() -> int:
    configured = read_tool_versions()
    observed = {name: command_result(command) for name, command in observed_commands().items()}
    lockfiles = {
        name: {"path": name, "sha256": sha256(ROOT / name)}
        for name in ("pnpm-lock.yaml", "uv.lock")
    }
    report: dict[str, Any] = {
        "schema_version": "1",
        "repository": "LenGeas",
        "platform": platform.platform(),
        "configured_tools": configured,
        "declared_dependencies": declared_dependencies(),
        "lockfiles": lockfiles,
        "observed_tools": observed,
        "python_executable": sys.executable,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    required_files = [ROOT / ".tool-versions", ROOT / "package.json", ROOT / "pyproject.toml"]
    valid = all(path.is_file() for path in required_files)
    valid = valid and all(item["sha256"] for item in lockfiles.values())
    valid = valid and report["declared_dependencies"]["python"]["all_exact"]
    valid = valid and report["declared_dependencies"]["npm"]["all_exact"]
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
