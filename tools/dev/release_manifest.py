"""Generate an immutable release manifest from the current Git tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest(tag: str) -> dict[str, object]:
    tracked = [Path(line) for line in git("ls-files").splitlines() if line]
    files = [{"path": path.as_posix(), "sha256": file_digest(ROOT / path)} for path in tracked]
    return {
        "schema_version": "1.0.0",
        "artifact_type": "lengeas.release",
        "tag": tag,
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "created_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "files": files,
        "provenance": {
            "builder": "local-git-tree",
            "source": "git",
            "signature": "sigstore-keyless-required",
            "sbom": "spdx-json-required",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest(args.tag), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"PASS release manifest: {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
