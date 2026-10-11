"""Deterministic contract generation for Phase 01."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from canonical_json import canonical_text
from definition_schemas import main as generate_definition_schemas
from generate_definition_models import generate as generate_definition_models
from typegen import generate_types

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCHEMA = ROOT / "packages" / "schemas"
GENERATED = ROOT / "packages" / "shared-types" / "generated"


def generate() -> None:
    generate_definition_schemas()
    generate_definition_models()
    GENERATED.mkdir(parents=True, exist_ok=True)
    vectors = sorted((SCHEMA / "canonical" / "vectors").glob("fixture_*.json"))
    index = {
        "generator": "lengeas-contract-generator",
        "version": "0.1.0",
        "vectors": [path.name for path in vectors],
    }
    (GENERATED / "generation-index.json").write_text(
        canonical_text(index) + "\n", encoding="utf-8", newline="\n"
    )
    for source in vectors:
        data = json.loads(source.read_text(encoding="utf-8"))
        output = GENERATED / f"{source.stem}.canonical.json"
        output.write_text(data["canonical_utf8"] + "\n", encoding="utf-8", newline="\n")
    generate_types()
    # The checked-in API contract is generated from the actual FastAPI route graph.
    from apps.api.app.main import create_app

    openapi = create_app(test_mode=True).openapi()
    (SCHEMA / "api" / "v1" / "openapi.json").write_text(
        json.dumps(openapi, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate()
