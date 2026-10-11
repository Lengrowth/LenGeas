"""Generate Python/TypeScript definition contracts and the reference index."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "packages/schemas/definition/v0.1/bundle.schema.json"
PYTHON_OUT = ROOT / "packages/sdk-python/definition_v0_1.py"
TS_OUT = ROOT / "packages/sdk-typescript/src/definition-v0_1.ts"
DOC_OUT = ROOT / "docs/reference/definition-schema-v0.1.md"


def resolve_name(schema: Any) -> str | None:
    if isinstance(schema, dict) and "$ref" in schema:
        reference = schema["$ref"]
        if isinstance(reference, str):
            return reference.rsplit("/", 1)[-1]
    return None


def python_type(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "Any"
    if "const" in schema:
        value = schema["const"]
        if isinstance(value, str):
            return f"Literal[{value!r}]"
        if isinstance(value, bool):
            return f"Literal[{value}]"
        return "int"
    if "enum" in schema:
        values = ", ".join(repr(value) for value in schema["enum"])
        return f"Literal[{values}]"
    name = resolve_name(schema)
    if name:
        return name
    if "oneOf" in schema or "anyOf" in schema:
        variants = schema.get("oneOf") or schema.get("anyOf") or []
        return " | ".join(dict.fromkeys(python_type(item) for item in variants)) or "Any"
    if schema.get("type") == "array":
        return f"list[{python_type(schema.get('items', {}))}]"
    if schema.get("type") == "object":
        return "dict[str, Any]"
    type_name = schema.get("type")
    return (
        {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "null": "None",
        }.get(type_name, "Any")
        if isinstance(type_name, str)
        else "Any"
    )


def ts_type(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "unknown"
    if "const" in schema:
        return json.dumps(schema["const"], ensure_ascii=False)
    if "enum" in schema:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in schema["enum"])
    name = resolve_name(schema)
    if name:
        return name
    if "oneOf" in schema or "anyOf" in schema:
        variants = schema.get("oneOf") or schema.get("anyOf") or []
        return " | ".join(dict.fromkeys(ts_type(item) for item in variants)) or "unknown"
    if schema.get("type") == "array":
        return f"{ts_type(schema.get('items', {}))}[]"
    if schema.get("type") == "object":
        return "Record<string, unknown>"
    type_name = schema.get("type")
    return (
        {
            "string": "string",
            "integer": "number",
            "number": "number",
            "boolean": "boolean",
            "null": "null",
        }.get(type_name, "unknown")
        if isinstance(type_name, str)
        else "unknown"
    )


def generate() -> None:
    root = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    defs: dict[str, Any] = root["$defs"]
    py: list[str] = [
        '"""Generated definition v0.1 model shapes. Do not edit."""',
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal, NotRequired, Required, TypedDict",
        "",
    ]
    ts: list[str] = [
        "// Generated from packages/schemas/definition/v0.1/bundle.schema.json. Do not edit.",
        "",
    ]
    rows = [
        "# Definition schema v0.1 reference",
        "",
        "Generated from `packages/schemas/definition/v0.1/bundle.schema.json`.",
        "",
        "| Definition | Required fields |",
        "|---|---|",
    ]
    aliases = [
        name
        for name, definition in defs.items()
        if not isinstance(definition.get("properties"), dict)
    ]
    for name in aliases:
        py.append(f"{name} = {python_type(defs[name])}")
        ts.append(f"export type {name} = {ts_type(defs[name])};")
    if aliases:
        py.append("")
        ts.append("")
    for name, definition in defs.items():
        props = definition.get("properties")
        if not isinstance(props, dict):
            continue
        required = set(definition.get("required", []))
        py.append(f"class {name}(TypedDict, total=False):")
        ts.append(f"export interface {name} {{")
        for key, field in props.items():
            safe_key = key if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", key) else json.dumps(key)
            py_type = python_type(field)
            py.append(
                f"    {safe_key}: Required[{py_type}]"
                if key in required
                else f"    {safe_key}: NotRequired[{py_type}]"
            )
            optional = "" if key in required else "?"
            ts.append(f"  {safe_key}{optional}: {ts_type(field)};")
        py.append("")
        ts.append("}")
        ts.append("")
        rows.append(
            f"| `{name}` | {', '.join(f'`{field}`' for field in sorted(required)) or '—'} |"
        )
    py.append('SCHEMA_VERSION = "0.1.0"')
    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    PYTHON_OUT.write_text("\n".join(py) + "\n", encoding="utf-8")
    TS_OUT.write_text("\n".join(ts), encoding="utf-8")
    DOC_OUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    subprocess.run(
        ["uv", "run", "--frozen", "ruff", "format", str(PYTHON_OUT)],
        cwd=ROOT,
        check=True,
    )
    node = "pnpm.cmd" if sys.platform == "win32" else "pnpm"
    subprocess.run([node, "exec", "prettier", "--write", str(TS_OUT)], cwd=ROOT, check=True)


if __name__ == "__main__":
    generate()
