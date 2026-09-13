[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$required = @(
  'README.md',
  'docs/phases/00-charter-and-architecture-lock.md',
  'docs/evidence/phase-00/manifest.json',
  'docs/evidence/phase-00/coverage.json',
  'docs/evidence/phase-00/test-report.xml',
  'docs/evidence/phase-00/architecture-review-minutes.md',
  'docs/governance/requirement-register.yaml',
  'docs/governance/requirements.yaml',
  'docs/governance/traceability-matrix.generated.md'
)
foreach ($path in $required) {
  if (-not (Test-Path (Join-Path $root $path) -PathType Leaf)) {
    throw "Missing required Phase 00 artifact: $path"
  }
}

$env:LENGEAS_GATE_ROOT = $root
$validation = @'
import hashlib
import json
import os
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

import jsonschema
import yaml

root = pathlib.Path(os.environ["LENGEAS_GATE_ROOT"])
pairs = [
    ("docs/governance/ownership.yaml", "docs/governance/schemas/ownership.schema.json"),
    ("docs/governance/requirement-register.yaml", "docs/governance/schemas/requirement-register.schema.json"),
    ("docs/governance/requirements.yaml", "docs/governance/schemas/requirements.schema.json"),
    ("docs/governance/risk-register.yaml", "docs/governance/schemas/risk-register.schema.json"),
    ("docs/governance/scope-register.yaml", "docs/governance/schemas/scope-register.schema.json"),
    ("docs/governance/vendor-register.yaml", "docs/governance/schemas/vendor-register.schema.json"),
]
for document, schema in pairs:
    validator = jsonschema.Draft202012Validator(json.loads((root / schema).read_text(encoding="utf-8")))
    validator.validate(yaml.safe_load((root / document).read_text(encoding="utf-8")))

manifest = json.loads((root / "docs/evidence/phase-00/manifest.json").read_text(encoding="utf-8"))
coverage = json.loads((root / "docs/evidence/phase-00/coverage.json").read_text(encoding="utf-8"))
ET.parse(root / "docs/evidence/phase-00/test-report.xml")
[json.loads(line) for line in (root / "docs/evidence/phase-00/commands.ndjson").read_text(encoding="utf-8").splitlines() if line.strip()]
assert manifest["status"] in {"in_review", "accepted"}
assert coverage["requirements_mapped"] == {"total": 25, "mapped": 25, "unmapped": 0}
assert coverage["mandatory_controls_mapped"] == {"total": 24, "mapped": 24, "unmapped": 0}

register = yaml.safe_load((root / "docs/governance/requirement-register.yaml").read_text(encoding="utf-8"))
generated = yaml.safe_load((root / "docs/governance/requirements.yaml").read_text(encoding="utf-8"))
matrix = {}
for line in (root / "docs/23-traceability-matrix.md").read_text(encoding="utf-8").splitlines():
    cells = [cell.strip() for cell in line.strip().split("|")]
    if len(cells) >= 5 and re.match(r"^RQ-\d{3}\b", cells[1]):
        requirement_id = re.match(r"^(RQ-\d{3})", cells[1]).group(1)
        matrix[requirement_id] = {int(value.strip()) for value in cells[3].split(",")}
assert len(matrix) == 25
for source, derived in zip(register["requirements"], generated["requirements"]):
    assert source["id"] == derived["id"]
    assert source["phase_tasks"] == derived["phase_tasks"]
    phases = {int(task[1:3]) for task in source["phase_tasks"] if not task.startswith("P00-")}
    assert phases == (matrix[source["id"]] - {0}), (source["id"], phases, matrix[source["id"]] - {0})
assert [row["id"] for row in register["mandatory_controls"]] == [f"MC-{index:03d}" for index in range(1, 25)]
orphan_id = "RQ-" + "027"
assert all(orphan_id not in path.read_text(encoding="utf-8", errors="ignore") for path in (root / "docs").rglob("*") if path.is_file())

for artifact in manifest["artifacts"]:
    path = artifact["path"]
    if path in {"docs/governance", "docs/architecture", "docs/decisions", "docs/evidence/phase-00"}:
        files = sorted(item for item in (root / path).rglob("*") if item.is_file() and not (path == "docs/evidence/phase-00" and item.name == "manifest.json"))
        payload = "".join(f"{item.relative_to(root).as_posix()}\t{hashlib.sha256(item.read_bytes()).hexdigest()}\n" for item in files).encode()
    else:
        payload = (root / path).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == artifact["sha256"], path

assert len(list((root / "docs/evidence/phase-00/tasks").glob("P00-T*.md"))) == 8
assert len(list((root / "docs/architecture/diagrams").glob("*.mmd"))) >= 11
assert not [path for path in subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines() if pathlib.Path(path).suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx", ".tf", ".tfvars", ".dockerfile"}]
print("PASS Phase 00 standalone gate: required artifacts, schemas, JSON/XML/NDJSON, traceability, hashes, diagrams, and product-code boundary")
'@

$validation | & python -
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
