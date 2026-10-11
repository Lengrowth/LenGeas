from __future__ import annotations

from typing import Any

from packages.schemas.definition_runtime import sha256_hex
from packages.schemas.definition_validation import _graph_cycle, validate_bundle


def valid_bundle() -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "blueprint": {
            "id": "blueprint_base",
            "schema_version": "0.1.0",
            "studio_id": "studio_main",
            "name": "Base Blueprint",
            "network_modes": ["offline"],
            "features": [],
            "allowed_modules": [],
            "required_modules": [],
            "resource_budget": {
                "max_formula_operations": 100,
                "max_condition_nodes": 100,
                "max_ast_depth": 32,
                "max_events_per_action": 100,
            },
        },
        "game": {
            "id": "game_main",
            "studio_id": "studio_main",
            "name": "Synthetic",
            "genre_labels": [],
            "default_locale": "en",
            "supported_locales": ["en"],
            "blueprint": "blueprint_base",
            "network_mode": "offline",
            "engine_range": "1.0.0",
            "modules": [],
            "features": [],
            "state_schema_version": "1",
            "definition_schema_version": "0.1.0",
        },
        "modules": [],
        "extension_manifest": {"schema_version": "0.1.0", "extensions": {}},
        "documents": [],
    }


def valid_module(module_id: str) -> dict[str, Any]:
    return {
        "id": module_id,
        "version": "1.0.0",
        "digest": "sha256:" + "a" * 64,
        "engine_range": "1.0.0",
        "requires": [],
        "conflicts": [],
        "configuration": {},
        "state_namespaces": [],
        "registered_actions": [],
        "subscribed_events": [],
        "emitted_events": [],
        "registered_conditions": [],
        "registered_effects": [],
        "registered_timers": [],
        "migrations": [],
        "resource_budget": {
            "max_formula_operations": 20,
            "max_condition_nodes": 20,
            "max_ast_depth": 20,
            "max_events_per_action": 10,
        },
    }


def valid_resource() -> dict[str, Any]:
    return {
        "id": "resource_coin",
        "schema_version": "0.1.0",
        "tags": ["currency"],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "resource_type": "currency",
        "numeric_model": {"type": "integer"},
        "initial_amount": 0,
        "minimum": 0,
        "maximum": 100,
        "overflow_policy": "reject",
        "visibility": "public",
        "transfer_policy": "non_transferable",
    }


def valid_formula(expression: dict[str, Any], variables: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": "formula_damage",
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "expression": expression,
        "variables": variables or [],
    }


def valid_progression(
    identifier: str,
    *,
    children: list[str] | None = None,
    dependencies: list[str] | None = None,
    entry: bool = False,
    required: bool = False,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "graph_id": "progression_main",
        "node_type": "root" if entry else "node",
        "requirements": [],
        "costs": [],
        "rewards": [],
        "effects": [],
        "dependencies": dependencies or [],
        "exclusive_group": "group_main",
        "repeat_policy": "never",
        "children": children or [],
        "entry": entry,
        "required": required,
    }


def valid_item(identifier: str = "item_coin") -> dict[str, Any]:
    return {
        "id": identifier,
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "item_type": "stackable",
        "stack_limit": 99,
        "properties": {},
    }


def valid_inventory(accepted_items: list[str]) -> dict[str, Any]:
    return {
        "id": "inventory_main",
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "owner_type": "player",
        "slot_limit": 20,
        "accepted_items": accepted_items,
    }


def test_valid_bundle_reports_definition_validity_without_claiming_staging_readiness() -> None:
    result = validate_bundle(valid_bundle())
    assert result["valid"] is True
    assert result["staging_eligible"] is False
    assert [level["level"] for level in result["levels"]] == [
        "syntax",
        "references",
        "graph",
        "semantic",
        "safety",
        "runtime",
        "simulation",
    ]
    assert [level["status"] for level in result["levels"]] == [
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
        "conformance_only",
        "conformance_only",
    ]


def test_graph_cycle_check_handles_long_acyclic_graph_without_recursion() -> None:
    graph = {f"node_{index}": [f"node_{index + 1}"] for index in range(1500)}
    graph["node_1500"] = []
    assert _graph_cycle(graph) is False


def test_blueprint_constrains_network_mode_and_features() -> None:
    bundle = valid_bundle()
    bundle["game"]["network_mode"] = "server_authoritative"
    bundle["game"]["features"] = ["feature_ranked"]
    result = validate_bundle(bundle)
    codes = {error["code"] for error in result["errors"]}
    assert "blueprint_network_mode_forbidden" in codes
    assert "blueprint_feature_forbidden" in codes


def test_module_dependency_cycle_is_rejected() -> None:
    bundle = valid_bundle()
    module = valid_module("module_alpha")
    module["requires"] = [{"module_id": "module_beta", "version_range": "*"}]
    other = valid_module("module_beta")
    other["requires"] = [{"module_id": "module_alpha", "version_range": "*"}]
    bundle["modules"] = [module, other]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha", "module_beta"]
    bundle["game"]["modules"] = [
        {"module_id": item["id"], "version": item["version"], "digest": item["digest"]}
        for item in bundle["modules"]
    ]
    result = validate_bundle(bundle)
    assert result["valid"] is False
    assert {error["code"] for error in result["errors"]} == {"dependency_cycle"}


def test_missing_module_dependency_is_rejected() -> None:
    bundle = valid_bundle()
    module = valid_module("module_alpha")
    module["requires"] = [{"module_id": "module_missing", "version_range": "^1.0.0"}]
    bundle["modules"] = [module]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha"]
    bundle["game"]["modules"] = [
        {"module_id": module["id"], "version": module["version"], "digest": module["digest"]}
    ]
    result = validate_bundle(bundle)
    assert "dependency_missing" in {error["code"] for error in result["errors"]}


def test_module_dependency_range_must_match_installed_version() -> None:
    bundle = valid_bundle()
    first = valid_module("module_alpha")
    first["requires"] = [{"module_id": "module_beta", "version_range": "^1.2.0"}]
    second = valid_module("module_beta")
    second["version"] = "2.0.0"
    bundle["modules"] = [first, second]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha", "module_beta"]
    bundle["game"]["modules"] = [
        {"module_id": item["id"], "version": item["version"], "digest": item["digest"]}
        for item in bundle["modules"]
    ]
    result = validate_bundle(bundle)
    assert "dependency_version_mismatch" in {error["code"] for error in result["errors"]}


def test_module_dependency_range_grammar_is_bounded() -> None:
    bundle = valid_bundle()
    first = valid_module("module_alpha")
    first["requires"] = [{"module_id": "module_beta", "version_range": ">=1.0.0"}]
    second = valid_module("module_beta")
    bundle["modules"] = [first, second]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha", "module_beta"]
    bundle["game"]["modules"] = [
        {"module_id": item["id"], "version": item["version"], "digest": item["digest"]}
        for item in bundle["modules"]
    ]
    result = validate_bundle(bundle)
    assert "dependency_version_range_invalid" in {error["code"] for error in result["errors"]}


def test_duplicate_module_ids_are_rejected() -> None:
    bundle = valid_bundle()
    module = valid_module("module_alpha")
    bundle["modules"] = [module, dict(module)]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha"]
    bundle["game"]["modules"] = [
        {"module_id": module["id"], "version": module["version"], "digest": module["digest"]}
    ]
    assert "duplicate_id" in {error["code"] for error in validate_bundle(bundle)["errors"]}


def test_required_module_must_be_allowed_by_blueprint() -> None:
    bundle = valid_bundle()
    bundle["blueprint"]["required_modules"] = ["module_required"]
    result = validate_bundle(bundle)
    assert "required_module_not_allowed" in {error["code"] for error in result["errors"]}


def test_module_release_lock_must_pin_exact_version_and_digest() -> None:
    bundle = valid_bundle()
    module = valid_module("module_alpha")
    bundle["modules"] = [module]
    bundle["game"]["modules"] = [
        {"module_id": module["id"], "version": "2.0.0", "digest": module["digest"]}
    ]
    result = validate_bundle(bundle)
    assert "release_lock_mismatch" in {error["code"] for error in result["errors"]}


def test_module_namespaces_have_one_owner() -> None:
    bundle = valid_bundle()
    first = valid_module("module_alpha")
    second = valid_module("module_beta")
    first["state_namespaces"] = ["shared_state"]
    second["state_namespaces"] = ["shared_state"]
    bundle["modules"] = [first, second]
    bundle["blueprint"]["allowed_modules"] = ["module_alpha", "module_beta"]
    bundle["game"]["modules"] = [
        {"module_id": item["id"], "version": item["version"], "digest": item["digest"]}
        for item in bundle["modules"]
    ]
    result = validate_bundle(bundle)
    assert "namespace_owned_by_multiple_modules" in {error["code"] for error in result["errors"]}


def test_effect_must_have_exactly_one_declared_owner() -> None:
    bundle = valid_bundle()
    effect = {
        "id": "effect_set_level",
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "operation": "set",
        "path": {"namespace_id": "state_main", "segments": ["level"]},
        "target": {"kind": "resource", "id": "resource_coin"},
        "value": 1,
    }
    bundle["documents"] = [effect, valid_resource()]
    result = validate_bundle(bundle)
    assert "effect_owner_invalid" in {error["code"] for error in result["errors"]}

    module = valid_module("module_effects")
    module["state_namespaces"] = ["state_main"]
    module["registered_effects"] = ["effect_set_level"]
    bundle["modules"] = [module]
    bundle["blueprint"]["allowed_modules"] = [module["id"]]
    bundle["game"]["modules"] = [
        {"module_id": module["id"], "version": module["version"], "digest": module["digest"]}
    ]
    assert validate_bundle(bundle)["valid"] is True


def test_installed_module_conflict_is_rejected() -> None:
    bundle = valid_bundle()
    first = valid_module("module_alpha")
    first["conflicts"] = ["module_beta"]
    second = valid_module("module_beta")
    bundle["modules"] = [first, second]
    bundle["game"]["modules"] = [
        {"module_id": item["id"], "version": item["version"], "digest": item["digest"]}
        for item in bundle["modules"]
    ]
    result = validate_bundle(bundle)
    assert "module_conflict_installed" in {error["code"] for error in result["errors"]}


def test_unregistered_extension_is_rejected() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {"setting": "on"}}
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "extension_unregistered" in {error["code"] for error in result["errors"]}


def test_registered_extension_schema_is_digest_pinned_and_validated() -> None:
    bundle = valid_bundle()
    schema = {
        "type": "object",
        "properties": {"setting": {"const": "on"}},
        "required": ["setting"],
        "additionalProperties": False,
    }
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": f"sha256:{sha256_hex(schema)}",
            "schema": schema,
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {"setting": "on"}}
    bundle["documents"] = [resource]
    assert validate_bundle(bundle)["valid"] is True


def test_extension_schema_accepts_resolvable_local_json_pointer_reference() -> None:
    bundle = valid_bundle()
    schema = {
        "$defs": {"setting": {"type": "string", "const": "on"}},
        "type": "object",
        "properties": {"setting": {"$ref": "#/$defs/setting"}},
        "required": ["setting"],
        "additionalProperties": False,
    }
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": f"sha256:{sha256_hex(schema)}",
            "schema": schema,
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {"setting": "on"}}
    bundle["documents"] = [resource]
    assert validate_bundle(bundle)["valid"] is True


def test_registered_extension_schema_digest_mismatch_is_rejected() -> None:
    bundle = valid_bundle()
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": "sha256:" + "0" * 64,
            "schema": {"type": "object"},
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {}}
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "extension_schema_digest_mismatch" in {error["code"] for error in result["errors"]}


def test_invalid_extension_schema_is_reported_without_running_it() -> None:
    bundle = valid_bundle()
    schema = {"type": "not-a-json-schema-type"}
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": f"sha256:{sha256_hex(schema)}",
            "schema": schema,
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {}}
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "extension_schema_invalid" in {error["code"] for error in result["errors"]}


def test_remote_extension_schema_reference_is_rejected() -> None:
    bundle = valid_bundle()
    schema = {"$ref": "https://example.invalid/schema.json"}
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": f"sha256:{sha256_hex(schema)}",
            "schema": schema,
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {}}
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "extension_schema_invalid" in {error["code"] for error in result["errors"]}


def test_extension_schema_with_unresolved_local_reference_is_rejected() -> None:
    bundle = valid_bundle()
    schema = {"$ref": "#/$defs/not_present"}
    bundle["extension_manifest"]["extensions"] = {
        "vendor.example": {
            "schema_id": "https://example.invalid/vendor.schema.json",
            "digest": f"sha256:{sha256_hex(schema)}",
            "schema": schema,
        }
    }
    resource = valid_resource()
    resource["extensions"] = {"vendor.example": {}}
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "extension_schema_invalid" in {error["code"] for error in result["errors"]}


def test_player_visible_resource_requires_supported_locale_keys() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["display_name_key"] = "resource.coin.name"
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "localization_key_missing" in {error["code"] for error in result["errors"]}


def test_impossible_resource_range_is_rejected() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["maximum"] = -1
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "impossible_range" in {error["code"] for error in result["errors"]}


def test_negative_resource_balance_requires_digest_bound_security_approval() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["minimum"] = -10
    bundle["documents"] = [resource]
    assert "negative_balance_approval_required" in {
        error["code"] for error in validate_bundle(bundle)["errors"]
    }
    unsigned = dict(resource)
    resource["negative_balance_approval"] = {
        "review_id": "review_123",
        "reviewer_role": "security_owner",
        "approved": True,
        "resource_digest": f"sha256:{sha256_hex(unsigned)}",
    }
    assert validate_bundle(bundle)["valid"] is True


def test_integer_resource_rejects_fractional_values() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["initial_amount"] = "1.5"
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "numeric_model_precision_mismatch" in {error["code"] for error in result["errors"]}


def test_route_to_resource_requires_explicit_target() -> None:
    bundle = valid_bundle()
    resource = valid_resource()
    resource["overflow_policy"] = "route_to_resource"
    bundle["documents"] = [resource]
    result = validate_bundle(bundle)
    assert "overflow_route_missing" in {error["code"] for error in result["errors"]}


def test_domain_reference_resolves_by_stable_id_and_kind() -> None:
    bundle = valid_bundle()
    bundle["documents"] = [valid_inventory(["item_coin"]), valid_item()]
    assert validate_bundle(bundle)["valid"] is True


def test_domain_reference_missing_target_is_rejected() -> None:
    bundle = valid_bundle()
    bundle["documents"] = [valid_inventory(["item_missing"])]
    assert "reference_missing" in {error["code"] for error in validate_bundle(bundle)["errors"]}


def test_formula_division_by_zero_is_rejected() -> None:
    bundle = valid_bundle()
    bundle["documents"] = [
        valid_formula(
            {
                "operator": "divide",
                "args": [
                    {"operator": "literal", "value": 1},
                    {"operator": "literal", "value": 0},
                ],
            }
        )
    ]
    result = validate_bundle(bundle)
    assert "division_by_zero" in {error["code"] for error in result["errors"]}


def test_formula_variables_are_allowlisted() -> None:
    bundle = valid_bundle()
    bundle["documents"] = [
        valid_formula({"operator": "variable", "name": "player_level"}, ["base_power"])
    ]
    result = validate_bundle(bundle)
    assert "formula_variable_not_allowed" in {error["code"] for error in result["errors"]}


def test_nested_formula_variables_are_allowlisted() -> None:
    bundle = valid_bundle()
    quantity = valid_formula({"operator": "variable", "name": "not_allowed"})
    cost = {
        "id": "cost_purchase",
        "schema_version": "0.1.0",
        "tags": [],
        "enabled": True,
        "metadata": {},
        "extensions": {},
        "owner": "player_owner",
        "target": {"kind": "resource", "id": "resource_coin"},
        "quantity": quantity,
        "insufficiency": "reject",
        "ledger_reason": "purchase",
    }
    bundle["documents"] = [valid_resource(), cost]
    result = validate_bundle(bundle)
    assert "formula_variable_not_allowed" in {error["code"] for error in result["errors"]}


def test_blueprint_formula_operation_budget_is_enforced() -> None:
    bundle = valid_bundle()
    bundle["blueprint"]["resource_budget"]["max_formula_operations"] = 2
    bundle["documents"] = [
        valid_formula(
            {
                "operator": "add",
                "args": [
                    {"operator": "literal", "value": 1},
                    {"operator": "literal", "value": 2},
                ],
            }
        )
    ]
    result = validate_bundle(bundle)
    assert "formula_operation_budget_exceeded" in {error["code"] for error in result["errors"]}


def test_piecewise_formula_branches_are_included_in_operation_budget() -> None:
    bundle = valid_bundle()
    bundle["blueprint"]["resource_budget"]["max_formula_operations"] = 3
    bundle["documents"] = [
        valid_formula(
            {
                "operator": "piecewise",
                "cases": [
                    {
                        "when": {"operator": "eq", "left": 1, "right": 1},
                        "then": {
                            "operator": "add",
                            "args": [
                                {"operator": "literal", "value": 1},
                                {"operator": "literal", "value": 2},
                            ],
                        },
                    }
                ],
                "fallback": {"operator": "literal", "value": 0},
            }
        )
    ]
    result = validate_bundle(bundle)
    assert "formula_operation_budget_exceeded" in {error["code"] for error in result["errors"]}


def test_formula_literal_rejects_negative_zero_decimal() -> None:
    bundle = valid_bundle()
    bundle["documents"] = [valid_formula({"operator": "literal", "value": "-0"})]
    result = validate_bundle(bundle)
    assert "decimal_not_normalized" in {error["code"] for error in result["errors"]}


def test_progression_cycle_and_required_unreachable_node_are_rejected() -> None:
    bundle = valid_bundle()
    first = valid_progression("node_alpha", children=["node_beta"], entry=True)
    second = valid_progression("node_beta", children=["node_alpha"])
    orphan = valid_progression("node_gamma", required=True)
    bundle["documents"] = [first, second, orphan]
    codes = {error["code"] for error in validate_bundle(bundle)["errors"]}
    assert "progression_cycle" in codes
    assert "progression_unreachable" in codes


def test_progression_dependency_cycle_is_rejected() -> None:
    bundle = valid_bundle()
    first = valid_progression("node_alpha", entry=True, dependencies=["node_beta"])
    second = valid_progression("node_beta", dependencies=["node_alpha"])
    bundle["documents"] = [first, second]
    result = validate_bundle(bundle)
    assert "progression_dependency_cycle" in {error["code"] for error in result["errors"]}


def test_recursive_reward_loop_is_rejected() -> None:
    bundle = valid_bundle()
    rewards = []
    for identifier, target in (("reward_alpha", "reward_beta"), ("reward_beta", "reward_alpha")):
        rewards.append(
            {
                "id": identifier,
                "schema_version": "0.1.0",
                "tags": [],
                "enabled": True,
                "metadata": {},
                "extensions": {},
                "entries": [{"kind": "reward", "id": target}],
            }
        )
    bundle["documents"] = rewards
    assert "reward_loop" in {error["code"] for error in validate_bundle(bundle)["errors"]}
