"""Create or verify a detached Ed25519 signature for the Definition v0.1 release."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "packages/schemas/definition/v0.1"
OUTPUT_ROOT = ROOT / "docs/evidence/phase-04/operations"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def catalog_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted(SCHEMA_ROOT.rglob("*.json")):
        digest.update(path.relative_to(SCHEMA_ROOT).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(hashlib.sha256(path.read_bytes()).hexdigest()))
    return digest.hexdigest()


def build_manifest() -> dict[str, object]:
    fixture_digest = (
        (ROOT / "tests/conformance/fixtures/definitions/valid/minimal-bundle/sha256.txt")
        .read_text(encoding="utf-8")
        .strip()
    )
    policy = ROOT / "docs/reference/definition-schema-compatibility.md"
    return {
        "artifact_type": "lengeas-definition-schema",
        "schema_version": "0.1.0",
        "schema_catalog_sha256": catalog_digest(),
        "minimal_bundle_sha256": fixture_digest,
        "python_model": "packages/sdk-python/definition_v0_1.py",
        "typescript_model": "packages/sdk-typescript/src/definition-v0_1.ts",
        "compatibility_policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
        "registry_status": "not_published",
    }


def sign(output_root: Path = OUTPUT_ROOT) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    payload = canonical_bytes(manifest)
    private_key = Ed25519PrivateKey.generate()
    signature = private_key.sign(payload)
    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    (output_root / "definition-schema-release.json").write_bytes(payload + b"\n")
    (output_root / "definition-schema-release.sig").write_text(
        base64.b64encode(signature).decode("ascii") + "\n", encoding="ascii"
    )
    (output_root / "definition-schema-release.pub.pem").write_bytes(pem)
    verify(output_root)


def verify(output_root: Path = OUTPUT_ROOT) -> None:
    payload = (output_root / "definition-schema-release.json").read_bytes().strip()
    signature = base64.b64decode(
        (output_root / "definition-schema-release.sig").read_text(encoding="ascii")
    )
    public_key = serialization.load_pem_public_key(
        (output_root / "definition-schema-release.pub.pem").read_bytes()
    )
    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("Release public key is not Ed25519.")
    public_key.verify(signature, payload)
    manifest = json.loads(payload)
    if manifest != build_manifest():
        raise ValueError("Signed release manifest is stale for the current schema catalog.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("sign", "verify"))
    args = parser.parse_args()
    if args.action == "sign":
        sign()
    else:
        verify()
    print(f"PASS definition schema release {args.action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
