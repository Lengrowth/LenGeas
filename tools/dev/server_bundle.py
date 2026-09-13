"""Build a server-only manifest for the pinned Compose deployment bundle.

This tool never invokes Docker. It checks the files and image digests that an
authorized server operator must transfer and verify before startup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = re.compile(r"^\s*image:\s+(?P<ref>[^\s]+)$")
REQUIRED = (
    "compose.yaml",
    ".env.example",
    "infrastructure/docker/api-shell/Dockerfile",
    "infrastructure/docker/api-shell/api_shell.py",
    "infrastructure/docker/otel-collector-config.yaml",
    "infrastructure/docker/prometheus.yml",
    "infrastructure/docker/grafana/provisioning/datasources/datasource.yaml",
    "infrastructure/docker/README.md",
    "infrastructure/docker/SERVER-DEPLOYMENT.md",
    "infrastructure/aws/Caddyfile",
    "infrastructure/aws/README.md",
    "infrastructure/aws/phase-01-user-data.sh",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("server bundle missing: " + ", ".join(missing))
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    images = [match.group("ref") for line in compose.splitlines() if (match := IMAGE.match(line))]
    unpinned = [ref for ref in images if "@sha256:" not in ref]
    if unpinned:
        raise SystemExit("server bundle contains unpinned images: " + ", ".join(unpinned))
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": "1.0.0",
        "bundle_type": "lengeas.phase-01.server-compose",
        "execution_policy": "server-only; Docker is not invoked by this tool",
        "source_commit": git_head(),
        "files": [{"path": path, "sha256": sha256(ROOT / path)} for path in REQUIRED],
        "image_digests": images,
        "verification": [
            "docker compose config --quiet",
            "python tools/dev/task_runner.py local-up",
            "python tools/dev/task_runner.py local-smoke",
            "python tools/dev/task_runner.py local-down",
        ],
    }
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS server bundle manifest: {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
