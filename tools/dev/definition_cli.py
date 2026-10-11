"""Validate and canonicalize synthetic definition packages."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCHEMA_ROOT = json.loads(
    (ROOT / "packages/schemas/definition/v0.1/bundle.schema.json").read_text(encoding="utf-8")
)
PACKAGE_MANIFEST_SCHEMA = {**SCHEMA_ROOT, "$ref": "#/$defs/PackageManifest"}

from packages.schemas.definition_runtime import (  # noqa: E402, I001
    DefinitionInputError,
    MAX_BUNDLE_BYTES,
    canonical_bytes,
    parse_yaml,
    sha256_hex,
    validate_document,
)
from packages.schemas.definition_validation import (  # noqa: E402, I001
    validate_bundle,
    validate_yaml,
)


def validate_fixtures() -> bool:
    fixture_root = ROOT / "tests/conformance/fixtures/definitions"
    passed = True
    for fixture in sorted((fixture_root / "invalid").glob("*/")):
        source = (fixture / "input.yaml").read_text(encoding="utf-8")
        schema_ref = fixture / "schema-ref.txt"
        if schema_ref.exists():
            authored = parse_yaml(source)
            result = {
                "errors": validate_document(
                    authored,
                    {
                        **SCHEMA_ROOT,
                        "$ref": f"#/$defs/{schema_ref.read_text(encoding='utf-8').strip()}",
                    },
                )
            }
        else:
            result = validate_yaml(source)
        expected = json.loads((fixture / "expected-errors.json").read_text(encoding="utf-8"))
        actual = result["errors"]
        if actual != expected:
            print(f"FAIL {fixture.name}: expected={expected!r}, actual={actual!r}")
            passed = False
        else:
            print(f"PASS invalid/{fixture.name}")
    for fixture in sorted((fixture_root / "valid").glob("*/")):
        if (fixture / "manifest.yaml").exists():
            authored = load_package(fixture)
        else:
            authored = parse_yaml((fixture / "input.yaml").read_text(encoding="utf-8"))
        schema_ref = fixture / "schema-ref.txt"
        if schema_ref.exists():
            validation_errors = validate_document(
                authored,
                {
                    **SCHEMA_ROOT,
                    "$ref": f"#/$defs/{schema_ref.read_text(encoding='utf-8').strip()}",
                },
            )
            if validation_errors:
                print(f"FAIL valid/{fixture.name}: schema validation failed {validation_errors!r}")
                passed = False
        canonical = canonical_bytes(authored)
        expected = (fixture / "canonical.json").read_bytes().strip()
        digest = (fixture / "sha256.txt").read_text(encoding="utf-8").strip()
        if canonical != expected or sha256_hex(authored) != digest:
            print(f"FAIL valid/{fixture.name}: canonical bytes or digest differ")
            passed = False
        elif "game" in authored and not validate_bundle(authored)["valid"]:
            print(f"FAIL valid/{fixture.name}: bundle schema/semantics invalid")
            passed = False
        else:
            print(f"PASS valid/{fixture.name}")
    return passed


def _read_package_yaml(package_root: Path, relative: str) -> Any:
    path = _package_file(package_root, relative)
    try:
        source = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise DefinitionInputError("yaml_encoding_invalid", "YAML input must be UTF-8.") from error
    return parse_yaml(source)


def _package_file(package_root: Path, relative: str) -> Path:
    path = (package_root / relative).resolve()
    if not path.is_relative_to(package_root.resolve()) or not path.is_file():
        raise ValueError("Package manifest path must identify a file within the package root.")
    return path


def load_package(package_root: Path) -> dict[str, Any]:
    """Resolve manifest-referenced YAML documents into the canonical bundle shape."""
    manifest = _read_package_yaml(package_root, "manifest.yaml")
    if not isinstance(manifest, dict):
        raise ValueError("Package manifest must be an object.")
    manifest_errors = validate_document(manifest, PACKAGE_MANIFEST_SCHEMA)
    if manifest_errors:
        raise ValueError(f"Package manifest is invalid: {manifest_errors}")
    referenced = [
        manifest["game"],
        manifest["blueprint"],
        manifest["extension_manifest"],
        *manifest["modules"],
        *manifest["documents"],
    ]
    total_bytes = (package_root / "manifest.yaml").stat().st_size + sum(
        _package_file(package_root, relative).stat().st_size for relative in referenced
    )
    if total_bytes > MAX_BUNDLE_BYTES:
        raise ValueError("Definition package exceeds the total byte limit.")
    game = _read_package_yaml(package_root, manifest["game"])
    blueprint = _read_package_yaml(package_root, manifest["blueprint"])
    modules = [_read_package_yaml(package_root, path) for path in manifest.get("modules", [])]
    documents = [_read_package_yaml(package_root, path) for path in manifest.get("documents", [])]
    extensions = _read_package_yaml(package_root, manifest["extension_manifest"])
    modules.sort(key=lambda item: item["id"])
    documents.sort(key=lambda item: (item["id"], canonical_bytes(item)))
    bundle = {
        "schema_version": manifest["schema_version"],
        "blueprint": blueprint,
        "game": game,
        "modules": modules,
        "extension_manifest": extensions,
        "documents": documents,
    }
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("path", type=Path)
    canonicalize = commands.add_parser("canonicalize")
    canonicalize.add_argument("path", type=Path)
    package = commands.add_parser("canonicalize-package")
    package.add_argument("path", type=Path)
    package.add_argument("--output", type=Path)
    commands.add_parser("fixtures")
    commands.add_parser("schemas")
    commands.add_parser("compatibility")
    commands.add_parser("determinism")
    commands.add_parser("tests")
    args = parser.parse_args()
    if args.command == "fixtures":
        return 0 if validate_fixtures() else 1
    if args.command == "schemas":
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

        for schema_path in sorted(
            (ROOT / "packages/schemas/definition/v0.1").rglob("*.schema.json")
        ):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            reference = schema.get("$ref", "")
            if "#/$defs/" in reference:
                name = reference.rsplit("#/$defs/", 1)[1]
                if name not in SCHEMA_ROOT["$defs"]:
                    raise SystemExit(
                        f"unresolved definition reference in {schema_path}: {reference}"
                    )
            print(f"PASS schema {schema_path.relative_to(ROOT)}")
        return 0
    if args.command == "compatibility":
        policy_path = ROOT / "docs/reference/definition-schema-compatibility.md"
        policy = policy_path.read_text(encoding="utf-8")
        expected = {
            "StableId",
            "Header",
            "ExtensionManifest",
            "PackageManifest",
            "Reference",
            "StatePath",
            "Game",
            "Blueprint",
            "Module",
            "Entity",
            "Resource",
            "Condition",
            "Formula",
            "Action",
            "Cost",
            "Effect",
            "Reward",
            "Event",
            "Timer",
            "ProgressionNode",
            "Item",
            "Inventory",
            "Quest",
            "Achievement",
            "Entitlement",
            "Localization",
            "LiveOps",
            "Experiment",
            "Analytics",
            "Save",
            "Match",
            "CrossGameContract",
            "ConditionNode",
            "FormulaNode",
        }
        missing = sorted(expected - SCHEMA_ROOT["$defs"].keys())
        if missing or not all(marker in policy for marker in ("Patch", "Minor", "Major")):
            print(f"FAIL schema compatibility: missing={missing}")
            return 1
        print("PASS schema compatibility policy and required v0.1 definitions")
        return 0
    if args.command == "determinism":
        fixture = ROOT / "tests/conformance/fixtures/definitions/valid/minimal-bundle"
        bundle = load_package(fixture)
        first = canonical_bytes(bundle)
        second = canonical_bytes(load_package(fixture))
        digest = sha256_hex(bundle)
        expected_digest = (fixture / "sha256.txt").read_text(encoding="utf-8").strip()
        if first != second or digest != expected_digest:
            print("FAIL canonical bundle determinism")
            return 1
        print(digest)
        return 0
    if args.command == "tests":
        test_result = subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-q",
                "tests/unit/definitions",
                "tests/security/definitions",
            ],
            cwd=ROOT,
            check=False,
        )
        return test_result.returncode
    if args.command == "canonicalize-package":
        try:
            bundle = load_package(args.path)
        except (OSError, ValueError):
            print(
                json.dumps(
                    {"errors": [{"pointer": "", "code": "package_invalid", "severity": "error"}]}
                )
            )
            return 1
        validation_result = validate_bundle(bundle)
        if not validation_result["valid"]:
            print(json.dumps(validation_result, indent=2, sort_keys=True))
            return 1
        canonical = canonical_bytes(bundle)
        output = args.output or args.path / "canonical.json"
        output.write_bytes(canonical + b"\n")
        readback = json.loads(output.read_bytes())
        if not validate_bundle(readback)["valid"] or canonical_bytes(readback) != canonical:
            print("FAIL canonical bundle read-back verification")
            return 1
        (output.parent / "sha256.txt").write_text(
            sha256_hex(bundle) + "\n", encoding="utf-8", newline="\n"
        )
        print(sha256_hex(bundle))
        return 0
    try:
        text = args.path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        print(
            json.dumps(
                {"errors": [{"pointer": "", "code": "yaml_encoding_invalid", "severity": "error"}]}
            )
        )
        return 1
    if args.command == "canonicalize":
        value: Any = parse_yaml(text)
        print(canonical_bytes(value).decode("utf-8"))
        print(sha256_hex(value))
        return 0
    result = validate_yaml(text)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
