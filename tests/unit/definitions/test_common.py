from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from packages.schemas.definition_runtime import (
    MAX_ARRAY_ITEMS,
    MAX_BUNDLE_BYTES,
    MAX_NESTING_DEPTH,
    MAX_NODE_COUNT,
    MAX_SIGNED_INTEGER,
    MAX_STRING_LENGTH,
    MIN_SIGNED_INTEGER,
    DefinitionInputError,
    _inspect_events,
    canonical_bytes,
    normalize_decimal,
    parse_yaml,
    sha256_hex,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "packages/schemas/definition/v0.1/bundle.schema.json"


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("a: &x value\n", "yaml_anchor"),
        ("a: &x value\nb: *x\n", "yaml_alias"),
        ("a: !thing value\n", "yaml_custom_tag"),
        ("a: 1\na: 2\n", "duplicate_key"),
        ("a: .nan\n", "non_finite_number"),
        ("a: .inf\n", "non_finite_number"),
        ("a: 1.25\n", "decimal_as_string_required"),
        ("a: 2026-10-11\n", "implicit_timestamp"),
        ("1: value\n", "non_string_object_key"),
    ],
)
def test_restricted_yaml_rejections(source: str, code: str) -> None:
    with pytest.raises(DefinitionInputError) as error:
        parse_yaml(source)
    assert error.value.code == code


def test_common_schema_rejects_unknown_header_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        {**schema, "$ref": "#/$defs/Header"}, format_checker=FormatChecker()
    )
    header = {
        "id": "hero_main",
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "unexpected": True,
    }
    assert any(error.validator == "additionalProperties" for error in validator.iter_errors(header))


def test_canonical_json_is_sorted_and_utf8() -> None:
    assert canonical_bytes({"z": 1, "é": "ok", "a": 2}) == '{"a":2,"z":1,"é":"ok"}'.encode()
    assert (
        sha256_hex({"a": 1}) == "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )


@pytest.mark.parametrize("value", ["0", "1", "-10", "1.25", "-0.001"])
def test_canonical_decimal_accepts_normalized_values(value: str) -> None:
    assert normalize_decimal(value) == value


@pytest.mark.parametrize("value", ["+1", "01", "1.0", "-0", "1e2", "1.0000000000"])
def test_canonical_decimal_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(DefinitionInputError):
        normalize_decimal(value)


def test_ast_and_numeric_boundaries() -> None:
    assert (
        len(parse_yaml("value: '" + "x" * MAX_STRING_LENGTH + "'\n")["value"]) == MAX_STRING_LENGTH
    )
    assert (
        len(
            parse_yaml("values: [" + ",".join("0" for _ in range(MAX_ARRAY_ITEMS)) + "]\n")[
                "values"
            ]
        )
        == MAX_ARRAY_ITEMS
    )
    assert parse_yaml("value: " + str(MAX_SIGNED_INTEGER) + "\n")["value"] == MAX_SIGNED_INTEGER
    assert parse_yaml("value: " + str(MIN_SIGNED_INTEGER) + "\n")["value"] == MIN_SIGNED_INTEGER
    nested = "value: " + "[" * (MAX_NESTING_DEPTH - 1) + "0" + "]" * (MAX_NESTING_DEPTH - 1)
    assert parse_yaml(nested)["value"] is not None
    object_text = "\n".join(f"k{index}: 0" for index in range(MAX_ARRAY_ITEMS))
    assert len(parse_yaml(object_text)) == MAX_ARRAY_ITEMS
    assert normalize_decimal("1.222222223", max_scale=9) == "1.222222223"
    with pytest.raises(DefinitionInputError) as error:
        normalize_decimal("1.2222222223", max_scale=9)
    assert error.value.code == "numeric_scale_exceeded"


def test_node_budget_exact_and_over_limit() -> None:
    exact = "[" + ",".join("0" for _ in range(MAX_NODE_COUNT - 6)) + "]"
    _inspect_events(exact)
    over = "[" + ",".join("0" for _ in range(MAX_NODE_COUNT - 5)) + "]"
    with pytest.raises(DefinitionInputError) as error:
        _inspect_events(over)
    assert error.value.code == "node_budget_exceeded"


def test_byte_budget_exact_and_over_limit() -> None:
    assert parse_yaml("#" + "x" * (MAX_BUNDLE_BYTES - 2) + "\n") is None
    with pytest.raises(DefinitionInputError) as error:
        parse_yaml("#" + "x" * (MAX_BUNDLE_BYTES - 1) + "\n")
    assert error.value.code == "bundle_limit_exceeded"


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("value: '" + "x" * (MAX_STRING_LENGTH + 1) + "'\n", "string_limit_exceeded"),
        (
            "values: [" + ",".join("0" for _ in range(MAX_ARRAY_ITEMS + 1)) + "]\n",
            "array_limit_exceeded",
        ),
        pytest.param(
            "\n".join(f"k{index}: 0" for index in range(MAX_ARRAY_ITEMS + 1)),
            "object_limit_exceeded",
            id="object_limit",
        ),
        ("value: " + str(MAX_SIGNED_INTEGER + 1) + "\n", "numeric_overflow"),
        ("value: " + str(MIN_SIGNED_INTEGER - 1) + "\n", "numeric_overflow"),
        (
            "value: " + "[" * MAX_NESTING_DEPTH + "0" + "]" * MAX_NESTING_DEPTH,
            "nesting_limit_exceeded",
        ),
        pytest.param("x" * (MAX_BUNDLE_BYTES + 1), "bundle_limit_exceeded", id="bundle_limit"),
    ],
)
def test_ast_and_bundle_limit_rejections(source: str, code: str) -> None:
    with pytest.raises(DefinitionInputError) as error:
        parse_yaml(source)
    assert error.value.code == code


def test_common_tag_count_boundary() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator({**schema, "$ref": "#/$defs/Tags"})
    assert not list(validator.iter_errors([f"tag{index}" for index in range(32)]))
    assert list(validator.iter_errors([f"tag{index}" for index in range(33)]))
