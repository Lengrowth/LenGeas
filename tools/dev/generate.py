"""Deterministic contract generation for Phase 01."""

from __future__ import annotations

import json
from pathlib import Path

from canonical_json import canonical_text
from typegen import generate_types

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "packages" / "schemas"
GENERATED = ROOT / "packages" / "shared-types" / "generated"


def generate() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    vectors = sorted((SCHEMA / "canonical" / "vectors").glob("fixture_*.json"))
    index = {
        "generator": "lengeas-contract-generator",
        "version": "0.1.0",
        "vectors": [path.name for path in vectors],
    }
    (GENERATED / "generation-index.json").write_text(canonical_text(index) + "\n", encoding="utf-8")
    for source in vectors:
        data = json.loads(source.read_text(encoding="utf-8"))
        output = GENERATED / f"{source.stem}.canonical.json"
        output.write_text(data["canonical_utf8"] + "\n", encoding="utf-8")
    generate_types()


if __name__ == "__main__":
    generate()
