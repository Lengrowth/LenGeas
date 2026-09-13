"""Validate release metadata and optional Sigstore signatures."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--signature", type=Path)
    parser.add_argument("--certificate", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    required = {"schema_version", "artifact_type", "tag", "commit", "tree", "files", "provenance"}
    missing = sorted(required - data.keys())
    if missing:
        print(f"FAIL provenance: missing manifest fields {missing}", file=sys.stderr)
        return 1
    if data["provenance"].get("signature") != "sigstore-keyless-required":
        print("FAIL provenance: manifest does not require keyless signing", file=sys.stderr)
        return 1
    if args.signature or args.certificate:
        if shutil.which("cosign") is None:
            print("BLOCKED provenance: cosign is unavailable for signature verification", file=sys.stderr)
            return 2
        if not args.signature or not args.certificate:
            print("FAIL provenance: signature and certificate must be supplied together", file=sys.stderr)
            return 1
        result = subprocess.run(["cosign", "verify-blob", str(args.manifest), "--signature", str(args.signature), "--certificate", str(args.certificate)], check=False)
        return result.returncode
    print("PASS provenance metadata: immutable commit/tree and keyless signature requirement validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

