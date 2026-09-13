"""Generate a deterministic SPDX JSON inventory for tracked repository files."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    files: list[dict[str, object]] = []
    for value in sorted(path for path in paths if path):
        path = ROOT / value
        files.append(
            {
                "SPDXID": f"SPDXRef-File-{len(files) + 1:05d}",
                "fileName": value,
                "checksums": [{"algorithm": "SHA256", "checksumValue": digest(path)}],
            }
        )
    document = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "lengeas-platform-source",
        "documentNamespace": "https://sbom.lengeas.com/source",
        "creationInfo": {"created": "1970-01-01T00:00:00Z", "creators": ["Tool: lengeas-sbom"]},
        "files": files,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS SBOM: {output.relative_to(ROOT)} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
