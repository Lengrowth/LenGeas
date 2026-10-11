"""Cross-platform runner for the Phase 01 synthetic test projects.

The runner deliberately uses only the Python standard library. That keeps the
failure mode useful on a fresh machine: mandatory external suites report a
missing prerequisite instead of becoming an accidental pytest skip.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"


@dataclass(frozen=True)
class Dependency:
    name: str
    description: str


SUITES: dict[str, tuple[str, tuple[Dependency, ...]]] = {
    "unit": ("unit", ()),
    "property": ("property", ()),
    "contract": ("contract", ()),
    "integration": (
        "integration",
        (
            Dependency("docker", "Docker CLI"),
            Dependency("compose-file", "root compose.yaml"),
            Dependency("local-stack", "running Compose dependency stack"),
        ),
    ),
    "e2e": (
        "e2e",
        (
            Dependency("e2e-base-url", "LENGEAS_E2E_BASE_URL"),
            Dependency("e2e-guest-proof", "LENGEAS_E2E_GUEST_PROOF"),
            Dependency("e2e-device-key", "LENGEAS_E2E_DEVICE_PUBLIC_KEY"),
        ),
    ),
    "performance": ("performance", ()),
    "security": ("security", ()),
    "determinism": ("determinism", ()),
    "disaster-recovery": ("disaster-recovery", ()),
}

REQUIRED_CATEGORIES = {
    "positive": "test_positive_",
    "negative": "test_negative_",
    "failure": "test_failure_",
    "security": "test_security_",
    "determinism": "test_determinism_",
    "performance": "test_bounded_performance_",
}


def _fixture_module(suite: str) -> tuple[Path, Path]:
    directory_name, _ = SUITES[suite]
    suite_root = TESTS / directory_name
    projects = sorted(
        path for path in suite_root.iterdir() if path.is_dir() and path.name.startswith("fixture_")
    )
    if len(projects) != 1:
        raise RuntimeError(
            f"fixture policy failed for {suite}: expected exactly one fixture_ project, found "
            f"{len(projects)}"
        )
    modules = sorted(projects[0].glob("test_fixture_*.py"))
    if len(modules) != 1:
        raise RuntimeError(
            f"fixture policy failed for {suite}: expected exactly one test_fixture_*.py, "
            f"found {len(modules)}"
        )
    return projects[0], modules[0]


def _load_module(path: Path) -> ModuleType:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    module_name = f"lengeas_{path.parent.name}_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _dependency_available(dependency: Dependency, project: Path) -> tuple[bool, str]:
    if dependency.name == "docker":
        if shutil.which("docker") is None:
            return False, "Docker CLI was not found on PATH"
        return True, "Docker CLI found"
    if dependency.name == "compose-file":
        compose = ROOT / "compose.yaml"
        return compose.exists(), f"{compose} is {'present' if compose.exists() else 'missing'}"
    if dependency.name == "local-stack":
        docker = shutil.which("docker")
        if docker is None or not (ROOT / "compose.yaml").exists():
            return (
                False,
                "Docker Compose cannot inspect a stack before Docker and compose.yaml "
                "are available",
            )
        completed = subprocess.run(  # noqa: S603 - executable is resolved from PATH.
            [docker, "compose", "ps", "--status", "running", "--services"],  # noqa: S603
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip() or "compose ps failed"
            return False, detail
        running = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
        required = {"mongo", "rabbitmq", "redpanda", "minio", "otel-collector"}
        missing = sorted(required - running)
        if missing:
            return False, f"running Compose services missing: {', '.join(missing)}"
        return True, "required local dependency services are running"
    if dependency.name == "e2e-base-url":
        value = os.environ.get("LENGEAS_E2E_BASE_URL", "").strip()
        return (
            bool(value),
            "LENGEAS_E2E_BASE_URL is set" if value else "LENGEAS_E2E_BASE_URL is unset",
        )
    if dependency.name == "e2e-guest-proof":
        value = os.environ.get("LENGEAS_E2E_GUEST_PROOF", "").strip()
        return (
            bool(value),
            "LENGEAS_E2E_GUEST_PROOF is set" if value else "LENGEAS_E2E_GUEST_PROOF is unset",
        )
    if dependency.name == "e2e-device-key":
        value = os.environ.get("LENGEAS_E2E_DEVICE_PUBLIC_KEY", "").strip()
        return (
            bool(value),
            "LENGEAS_E2E_DEVICE_PUBLIC_KEY is set"
            if value
            else "LENGEAS_E2E_DEVICE_PUBLIC_KEY is unset",
        )
    return False, f"unknown dependency declaration: {dependency.name}"


def _validate_fixture_policy() -> None:
    categories: set[str] = set()
    for suite in SUITES:
        project, module_path = _fixture_module(suite)
        if not project.name.startswith("fixture_") or not module_path.name.startswith(
            "test_fixture_"
        ):
            raise RuntimeError(f"fixture policy failed: {module_path} is not fixture-prefixed")
        module = _load_module(module_path)
        if getattr(module, "SUITE", None) != suite:
            raise RuntimeError(f"{module_path}: SUITE metadata must be {suite!r}")
        fixture_files = sorted(project.glob("fixture_*.json"))
        if not fixture_files:
            raise RuntimeError(f"{project}: missing fixture_*.json synthetic input")
        test_methods = {
            method
            for candidate in vars(module).values()
            if isinstance(candidate, type) and issubclass(candidate, unittest.TestCase)
            for method in dir(candidate)
            if method.startswith("test_")
        }
        for name, prefix in REQUIRED_CATEGORIES.items():
            if any(method.startswith(prefix) for method in test_methods):
                categories.add(name)
        declared = tuple(getattr(module, "REQUIRED_DEPENDENCIES", ()))
        expected = tuple(dependency.name for dependency in SUITES[suite][1])
        if declared != expected:
            raise RuntimeError(
                f"{module_path}: dependency metadata {declared!r} does not match {expected!r}"
            )
    missing = sorted(set(REQUIRED_CATEGORIES) - categories)
    if missing:
        raise RuntimeError(f"fixture policy failed: missing check categories: {', '.join(missing)}")


def _identity_module(suite: str) -> Path:
    path = TESTS / SUITES[suite][0] / "identity"
    modules = sorted(path.glob("test_*.py")) if path.exists() else []
    if len(modules) != 1:
        raise RuntimeError(f"identity test policy failed for {suite}: expected one identity module")
    return modules[0]


def _is_identity_selector(selector: str | None) -> bool:
    if not selector:
        return False
    tokens = {token.strip().lower() for token in selector.split(",")}
    return bool(tokens & {"identity", "auth", "supabase", "mongodb", "tenancy", "authorization"})


def run_suite(suite: str, selector: str | None = None) -> int:
    if suite not in SUITES:
        suite_names = ", ".join(SUITES)
        print(f"ERROR unknown suite {suite!r}; expected one of: {suite_names}", file=sys.stderr)
        return 2
    try:
        project, module_path = _fixture_module(suite)
        paths = [_identity_module(suite)] if _is_identity_selector(selector) else [module_path]
        modules = [_load_module(path) for path in paths]
        _validate_fixture_policy()
    except (OSError, RuntimeError, ImportError, SyntaxError) as exc:
        print(f"ERROR {suite}: {exc}", file=sys.stderr)
        return 2

    # Integration and E2E selectors retain their real-system prerequisites.
    dependencies = (
        SUITES[suite][1]
        if suite in {"integration", "e2e"}
        else (() if _is_identity_selector(selector) else SUITES[suite][1])
    )
    unavailable = []
    for dependency in dependencies:
        available, detail = _dependency_available(dependency, project)
        print(f"DEPENDENCY {dependency.name}: {'PASS' if available else 'FAIL'} - {detail}")
        if not available:
            unavailable.append(f"{dependency.name} ({detail})")
    if unavailable:
        print(
            f"FAIL {suite}: mandatory dependency unavailable; suite failed, not skipped: "
            + "; ".join(unavailable),
            file=sys.stderr,
        )
        return 2

    loader = unittest.defaultTestLoader
    tests = unittest.TestSuite(loader.loadTestsFromModule(module) for module in modules)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0, buffer=True).run(tests)
    if result.wasSuccessful():
        label = {
            "integration": "backend integration checks",
            "e2e": "deployed API boundary checks",
        }.get(suite, "synthetic fixture checks")
        print(f"PASS {suite}: {result.testsRun} {label}")
        return 0
    print(stream.getvalue().rstrip(), file=sys.stderr)
    print(
        f"FAIL {suite}: {len(result.failures)} failure(s), {len(result.errors)} error(s); "
        "mandatory suite result is failed",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=[*SUITES, "all"], help="test project to execute")
    parser.add_argument("selector", nargs="?", help="optional identity selector")
    args = parser.parse_args()
    if args.suite == "all":
        try:
            _validate_fixture_policy()
        except (OSError, RuntimeError, ImportError, SyntaxError) as exc:
            print(f"ERROR fixture policy: {exc}", file=sys.stderr)
            return 2
        return max(run_suite(suite) for suite in SUITES)
    return run_suite(args.suite, args.selector)


if __name__ == "__main__":
    raise SystemExit(main())
