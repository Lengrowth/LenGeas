from __future__ import annotations

import pytest

from packages.schemas.definition_runtime import DefinitionInputError, parse_yaml


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("value: &x data\ncopy: *x\n", "yaml_alias"),
        ("value: !python/object/apply:os.system ['id']\n", "yaml_custom_tag"),
        ("value: .nan\n", "non_finite_number"),
        ("value: 1.5\n", "decimal_as_string_required"),
    ],
)
def test_security_rejects_unsafe_yaml_features(source: str, code: str) -> None:
    with pytest.raises(DefinitionInputError) as error:
        parse_yaml(source)
    assert error.value.code == code


def test_security_rejects_deep_yaml_before_object_construction() -> None:
    source = "value: " + "[" * 64 + "0" + "]" * 64
    with pytest.raises(DefinitionInputError) as error:
        parse_yaml(source)
    assert error.value.code == "nesting_limit_exceeded"
