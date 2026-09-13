"""Phase-specific gate that fails closed when review prerequisites are open."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    phase = sys.argv[1] if len(sys.argv) > 1 else "01"
    path = ROOT / "docs" / "evidence" / f"phase-{phase}" / "manifest.json"
    if not path.exists():
        print(f"FAIL phase gate: missing {path}", file=sys.stderr)
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8"))
    blockers = manifest.get("blockers", [])
    if manifest.get("status") != "in_review" or blockers:
        print(
            f"FAIL phase gate: status={manifest.get('status')!r}; blockers={blockers!r}",
            file=sys.stderr,
        )
        return 1
    print(f"PASS phase gate: Phase {phase} is in_review with no blockers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
