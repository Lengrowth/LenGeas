"""Strict parsing and canonical serialization for v0.1 definitions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from yaml.events import (  # type: ignore[import-untyped]
    AliasEvent,
    MappingEndEvent,
    MappingStartEvent,
    ScalarEvent,
    SequenceEndEvent,
    SequenceStartEvent,
)
from yaml.nodes import MappingNode, ScalarNode  # type: ignore[import-untyped]

MAX_BUNDLE_BYTES = 5 * 1024 * 1024
MAX_NESTING_DEPTH = 64
MAX_NODE_COUNT = 100_000
MAX_STRING_LENGTH = 4096
MAX_ARRAY_ITEMS = 4096
MAX_NUMERIC_SCALE = 9
MAX_SIGNED_INTEGER = 2**63 - 1
MIN_SIGNED_INTEGER = -(2**63)

_TIMESTAMP_SCALAR = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}(?:[Tt]|[ \t]+\d{1,2}:\d{2})")
_DECIMAL = re.compile(r"\A-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")
_BUILTIN_TAGS = {
    "tag:yaml.org,2002:str",
    "tag:yaml.org,2002:int",
    "tag:yaml.org,2002:float",
    "tag:yaml.org,2002:bool",
    "tag:yaml.org,2002:null",
}


class DefinitionInputError(ValueError):
    """A stable, client-safe definition input error."""

    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.pointer = pointer

    def as_dict(self) -> dict[str, str]:
        return {"pointer": self.pointer, "code": self.code, "severity": "error"}


class _StrictLoader(yaml.SafeLoader):  # type: ignore[misc]
    """SafeLoader that rejects non-string keys and duplicate mapping keys."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[str, Any]:
        if not isinstance(node, MappingNode):
            raise DefinitionInputError("yaml_type", "Expected a YAML object.")
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode) or key_node.tag != "tag:yaml.org,2002:str":
                raise DefinitionInputError("non_string_object_key", "Object keys must be strings.")
            key = cast(str, self.construct_object(key_node, deep=deep))
            if key in result:
                raise DefinitionInputError("duplicate_key", "Object keys must be unique.")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _inspect_events(text: str) -> None:
    depth = 0
    count = 0
    anchor_seen = False
    try:
        for event in yaml.parse(text, Loader=_StrictLoader):
            count += 1
            if count > MAX_NODE_COUNT:
                raise DefinitionInputError("node_budget_exceeded", "YAML node budget exceeded.")
            if isinstance(event, AliasEvent):
                raise DefinitionInputError("yaml_alias", "YAML aliases are not supported.")
            if getattr(event, "anchor", None) is not None:
                anchor_seen = True
            tag = getattr(event, "tag", None)
            if tag is not None and tag not in _BUILTIN_TAGS:
                raise DefinitionInputError("yaml_custom_tag", "Custom YAML tags are not supported.")
            if tag == "tag:yaml.org,2002:timestamp":
                raise DefinitionInputError(
                    "implicit_timestamp",
                    "YAML timestamps are not supported; use an explicit UTC string.",
                )
            if isinstance(event, ScalarEvent):
                if event.style is None and _TIMESTAMP_SCALAR.match(event.value):
                    raise DefinitionInputError(
                        "implicit_timestamp",
                        "YAML timestamps are not supported; use an explicit UTC string.",
                    )
                if len(event.value) > MAX_STRING_LENGTH:
                    raise DefinitionInputError("string_limit_exceeded", "String limit exceeded.")
            if isinstance(event, (MappingStartEvent, SequenceStartEvent)):
                depth += 1
                if depth > MAX_NESTING_DEPTH:
                    raise DefinitionInputError(
                        "nesting_limit_exceeded", "Nesting depth limit exceeded."
                    )
            elif isinstance(event, (MappingEndEvent, SequenceEndEvent)):
                depth -= 1
        if anchor_seen:
            raise DefinitionInputError("yaml_anchor", "YAML anchors are not supported.")
    except DefinitionInputError:
        raise
    except yaml.YAMLError as error:
        raise DefinitionInputError("yaml_syntax", "YAML syntax is invalid.") from error


def _validate_value(value: Any, depth: int = 0) -> None:
    if depth > MAX_NESTING_DEPTH:
        raise DefinitionInputError("nesting_limit_exceeded", "Nesting depth limit exceeded.")
    if isinstance(value, (datetime, date)):
        raise DefinitionInputError(
            "implicit_timestamp", "YAML timestamps are not supported; use an explicit UTC string."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise DefinitionInputError("non_finite_number", "NaN and infinity are not supported.")
    if isinstance(value, float):
        raise DefinitionInputError(
            "decimal_as_string_required", "Fixed-decimal values must use normalized strings."
        )
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and not MIN_SIGNED_INTEGER <= value <= MAX_SIGNED_INTEGER
    ):
        raise DefinitionInputError("numeric_overflow", "Integer exceeds the signed 64-bit range.")
    if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
        raise DefinitionInputError("string_limit_exceeded", "String limit exceeded.")
    if isinstance(value, dict):
        if len(value) > MAX_ARRAY_ITEMS:
            raise DefinitionInputError("object_limit_exceeded", "Object size limit exceeded.")
        for key, item in value.items():
            if not isinstance(key, str):
                raise DefinitionInputError("non_string_object_key", "Object keys must be strings.")
            _validate_value(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > MAX_ARRAY_ITEMS:
            raise DefinitionInputError("array_limit_exceeded", "Array size limit exceeded.")
        for item in value:
            _validate_value(item, depth + 1)


def parse_yaml(text: str) -> Any:
    """Parse the restricted YAML subset used by definition packages."""
    if len(text.encode("utf-8")) > MAX_BUNDLE_BYTES:
        raise DefinitionInputError(
            "bundle_limit_exceeded", "Definition document exceeds the byte limit."
        )
    _inspect_events(text)
    try:
        value = yaml.load(text, Loader=_StrictLoader)
    except DefinitionInputError:
        raise
    except yaml.YAMLError as error:
        raise DefinitionInputError("yaml_syntax", "YAML syntax is invalid.") from error
    _validate_value(value)
    return value


def validate_document(value: Any, schema: dict[str, Any]) -> list[dict[str, str]]:
    """Return stable structured JSON Schema errors for a parsed document."""
    from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[dict[str, str]] = []
    for error in validator.iter_errors(value):
        pointer = "/" + "/".join(
            str(part).replace(chr(126), chr(126) + "0").replace("/", chr(126) + "1")
            for part in error.absolute_path
        )
        if pointer == "/":
            pointer = ""
        errors.append({"pointer": pointer, "code": "schema_validation", "severity": "error"})
    return sorted(errors, key=lambda item: (item["pointer"], item["code"]))


def normalize_decimal(value: str, *, max_scale: int = MAX_NUMERIC_SCALE) -> str:
    """Validate and return a normalized fixed-decimal string."""
    if not _DECIMAL.fullmatch(value) or value in {"-0", "-0.0"}:
        raise DefinitionInputError("decimal_not_normalized", "Decimal string is not canonical.")
    try:
        decimal = Decimal(value)
    except InvalidOperation as error:
        raise DefinitionInputError("decimal_invalid", "Decimal string is invalid.") from error
    exponent = decimal.as_tuple().exponent
    if not isinstance(exponent, int):
        raise DefinitionInputError("decimal_invalid", "Decimal exponent is invalid.")
    scale = max(0, -exponent)
    if scale > max_scale:
        raise DefinitionInputError(
            "numeric_scale_exceeded", "Decimal scale exceeds the supported limit."
        )
    if not decimal.is_finite():
        raise DefinitionInputError("non_finite_number", "NaN and infinity are not supported.")
    if decimal < MIN_SIGNED_INTEGER or decimal > MAX_SIGNED_INTEGER:
        raise DefinitionInputError("numeric_overflow", "Decimal value exceeds the supported range.")
    return value


def _json_safe(value: Any) -> None:
    if isinstance(value, (datetime, date)):
        raise DefinitionInputError("implicit_timestamp", "Timestamps must be explicit UTC strings.")
    if isinstance(value, float) and not math.isfinite(value):
        raise DefinitionInputError("non_finite_number", "NaN and infinity are not supported.")
    if isinstance(value, float):
        raise DefinitionInputError(
            "decimal_as_string_required", "Fixed-decimal values must use normalized strings."
        )
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise DefinitionInputError("non_string_object_key", "Object keys must be strings.")
            _json_safe(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _json_safe(item)


def canonical_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible values using the platform canonical JSON rules."""
    _json_safe(value)
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DefinitionInputError(
            "canonical_value_invalid", "Value cannot be canonicalized."
        ) from error


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
