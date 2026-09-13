"""OpenAPI compatibility gate foundation."""

from __future__ import annotations

import json
from pathlib import Path


def compare(baseline: Path, candidate: Path) -> list[str]:
    if not baseline.exists() or not candidate.exists():
        return ["OpenAPI baseline and candidate are both required"]
    if json.loads(baseline.read_text(encoding="utf-8")) != json.loads(candidate.read_text(encoding="utf-8")):
        return ["OpenAPI documents differ; review compatibility before release"]
    return []

