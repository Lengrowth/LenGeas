"""Build the checked-in definition v0.1 schema catalog from its shared source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "packages/schemas/definition/v0.1"
MASTER = BASE / "bundle.schema.json"


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required if required is not None else list(properties),
        "additionalProperties": False,
    }


def catalog() -> dict[str, Any]:
    defs: dict[str, Any] = {
        "StableId": {"type": "string", "pattern": "^[a-z][a-z0-9_]{2,63}$", "maxLength": 64},
        "SchemaVersion": {"type": "string", "const": "0.1.0"},
        "LocalizationKey": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_.-]{2,127}$",
            "maxLength": 128,
        },
        "Tag": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_.-]{0,63}$", "maxLength": 64},
        "Tags": {"type": "array", "items": ref("Tag"), "uniqueItems": True, "maxItems": 32},
        "Metadata": {
            "type": "object",
            "propertyNames": {"pattern": "^[a-z][a-z0-9_]{0,63}$"},
            "additionalProperties": {"type": "string", "maxLength": 256},
            "maxProperties": 128,
        },
        "Extensions": {
            "type": "object",
            "propertyNames": {"pattern": "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$"},
            "additionalProperties": True,
            "maxProperties": 64,
        },
        "Header": obj(
            {
                "id": ref("StableId"),
                "schema_version": ref("SchemaVersion"),
                "display_name_key": ref("LocalizationKey"),
                "description_key": ref("LocalizationKey"),
                "tags": ref("Tags"),
                "enabled": {"type": "boolean"},
                "metadata": ref("Metadata"),
                "extensions": ref("Extensions"),
            },
            ["id", "schema_version", "tags", "enabled", "metadata", "extensions"],
        ),
        "Timestamp": {
            "type": "string",
            "format": "date-time",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d{1,6})?Z$",
            "maxLength": 27,
        },
        "CanonicalDecimal": {
            "type": "string",
            "pattern": "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]*[1-9])?$",
            "maxLength": 32,
        },
        "IntegerValue": {"type": "integer", "minimum": -(2**63), "maximum": 2**63 - 1},
        "NumericValue": {"oneOf": [ref("IntegerValue"), ref("CanonicalDecimal")]},
        "NumericModel": {
            "oneOf": [
                obj({"type": {"const": "integer"}}),
                obj(
                    {
                        "type": {"const": "fixed_decimal"},
                        "scale": {"type": "integer", "minimum": 0, "maximum": 9},
                    }
                ),
            ]
        },
        "ReferenceKind": {
            "enum": [
                "game",
                "module",
                "entity",
                "resource",
                "condition",
                "formula",
                "action",
                "cost",
                "effect",
                "reward",
                "event",
                "timer",
                "relationship",
                "progression_node",
                "item",
                "quest",
                "achievement",
                "entitlement",
                "localization",
                "experiment",
                "save",
                "match",
                "cross_game_contract",
            ]
        },
        "Reference": obj({"kind": ref("ReferenceKind"), "id": ref("StableId")}),
        "StatePath": obj(
            {
                "namespace_id": ref("StableId"),
                "segments": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,63}$"},
                    "minItems": 1,
                    "maxItems": 32,
                },
            }
        ),
        "FormulaOperand": {
            "oneOf": [
                {"type": "integer"},
                {"type": "string", "maxLength": 4096},
                {"type": "boolean"},
                {"type": "null"},
                obj({"path": ref("StatePath")}),
            ]
        },
        "FormulaNode": {
            "oneOf": [
                obj({"operator": {"const": "literal"}, "value": ref("NumericValue")}),
                obj(
                    {
                        "operator": {"const": "variable"},
                        "name": {"type": "string", "minLength": 1, "maxLength": 128},
                    }
                ),
                *[
                    obj(
                        {
                            "operator": {"const": operator},
                            "args": {
                                "type": "array",
                                "items": ref("FormulaNode"),
                                "minItems": 2,
                                "maxItems": 256,
                            },
                        }
                    )
                    for operator in ("add", "subtract", "multiply", "divide", "min", "max")
                ],
                obj(
                    {
                        "operator": {"const": "clamp"},
                        "args": {
                            "type": "array",
                            "items": ref("FormulaNode"),
                            "minItems": 3,
                            "maxItems": 3,
                        },
                    }
                ),
                *[
                    obj(
                        {
                            "operator": {"const": operator},
                            "args": {
                                "type": "array",
                                "items": ref("FormulaNode"),
                                "minItems": 1,
                                "maxItems": 1,
                            },
                        }
                    )
                    for operator in ("floor", "ceil")
                ],
                obj(
                    {
                        "operator": {"const": "power_integer"},
                        "args": {
                            "type": "array",
                            "items": ref("FormulaNode"),
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    }
                ),
                obj(
                    {
                        "operator": {"const": "piecewise"},
                        "cases": {
                            "type": "array",
                            "items": obj(
                                {"when": ref("ConditionNode"), "then": ref("FormulaNode")}
                            ),
                            "minItems": 1,
                            "maxItems": 256,
                        },
                        "fallback": ref("FormulaNode"),
                    }
                ),
            ]
        },
        "ConditionNode": {
            "oneOf": [
                *[
                    obj(
                        {
                            "operator": {"const": operator},
                            "args": {
                                "type": "array",
                                "items": ref("ConditionNode"),
                                "minItems": 1,
                                "maxItems": 256,
                            },
                        }
                    )
                    for operator in ("all", "any")
                ],
                obj(
                    {
                        "operator": {"const": "not"},
                        "args": {
                            "type": "array",
                            "items": ref("ConditionNode"),
                            "minItems": 1,
                            "maxItems": 1,
                        },
                    }
                ),
                *[
                    obj(
                        {
                            "operator": {"const": operator},
                            "left": ref("FormulaOperand"),
                            "right": ref("FormulaOperand"),
                        }
                    )
                    for operator in ("eq", "ne", "lt", "lte", "gt", "gte")
                ],
                obj(
                    {
                        "operator": {"const": "in"},
                        "value": ref("FormulaOperand"),
                        "values": {
                            "type": "array",
                            "items": ref("FormulaOperand"),
                            "minItems": 1,
                            "maxItems": 256,
                        },
                    }
                ),
                obj({"operator": {"const": "exists"}, "path": ref("StatePath")}),
                *[
                    obj({"operator": {"const": operator}, "at": ref("Timestamp")})
                    for operator in ("before", "after")
                ],
                obj(
                    {
                        "operator": {"const": "elapsed_at_least"},
                        "path": ref("StatePath"),
                        "duration_seconds": {"type": "integer", "minimum": 0},
                    }
                ),
                obj(
                    {
                        "operator": {"const": "predicate"},
                        "name": ref("StableId"),
                        "arguments": {"type": "object"},
                    }
                ),
            ]
        },
        "NetworkMode": {
            "enum": [
                "offline",
                "offline_first",
                "online_optional",
                "online_required",
                "server_authoritative",
            ]
        },
        "Dependency": obj(
            {
                "module_id": ref("StableId"),
                "version_range": {"type": "string", "minLength": 1, "maxLength": 128},
            }
        ),
        "ReleaseLock": obj(
            {
                "module_id": ref("StableId"),
                "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
                "digest": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
            }
        ),
        "Blueprint": obj(
            {
                "id": ref("StableId"),
                "schema_version": ref("SchemaVersion"),
                "studio_id": ref("StableId"),
                "name": {"type": "string", "minLength": 1, "maxLength": 128},
                "network_modes": {
                    "type": "array",
                    "items": ref("NetworkMode"),
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "features": {"type": "array", "items": ref("StableId"), "uniqueItems": True},
                "allowed_modules": {"type": "array", "items": ref("StableId"), "uniqueItems": True},
                "required_modules": {
                    "type": "array",
                    "items": ref("StableId"),
                    "uniqueItems": True,
                },
                "resource_budget": ref("ResourceBudget"),
            }
        ),
        "ResourceBudget": obj(
            {
                "max_formula_operations": {"type": "integer", "minimum": 1, "maximum": 4096},
                "max_condition_nodes": {"type": "integer", "minimum": 1, "maximum": 256},
                "max_ast_depth": {"type": "integer", "minimum": 1, "maximum": 32},
                "max_events_per_action": {"type": "integer", "minimum": 0, "maximum": 256},
            }
        ),
        "ExtensionRegistration": obj(
            {
                "schema_id": {"type": "string", "minLength": 1, "maxLength": 256},
                "digest": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
                "schema": {"type": "object", "minProperties": 1},
            }
        ),
        "ExtensionManifest": obj(
            {
                "schema_version": ref("SchemaVersion"),
                "extensions": {
                    "type": "object",
                    "propertyNames": {"pattern": "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$"},
                    "additionalProperties": ref("ExtensionRegistration"),
                    "maxProperties": 64,
                },
            }
        ),
        "PackageManifest": obj(
            {
                "schema_version": ref("SchemaVersion"),
                "game": {
                    "type": "string",
                    "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$",
                },
                "blueprint": {
                    "type": "string",
                    "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$",
                },
                "modules": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$",
                    },
                    "maxItems": 128,
                },
                "extension_manifest": {
                    "type": "string",
                    "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$",
                },
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$",
                    },
                    "maxItems": 4096,
                },
            }
        ),
    }
    definitions: dict[str, Any] = {}
    primitive_fields: dict[str, dict[str, Any]] = {
        "Entity": {
            "entity_type": {"type": "string", "minLength": 1},
            "initial_state": {"type": "object"},
            "properties": {"type": "object"},
            "relationships": {"type": "array", "items": {"type": "object"}},
        },
        "Resource": {
            "resource_type": {"type": "string"},
            "numeric_model": ref("NumericModel"),
            "initial_amount": ref("NumericValue"),
            "minimum": ref("NumericValue"),
            "maximum": ref("NumericValue"),
            "overflow_policy": {"enum": ["reject", "clamp", "route_to_resource"]},
            "route_to_resource_id": ref("StableId"),
            "negative_balance_approval": obj(
                {
                    "review_id": ref("StableId"),
                    "reviewer_role": {"const": "security_owner"},
                    "approved": {"const": True},
                    "resource_digest": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
                }
            ),
            "visibility": {"enum": ["public", "private", "server_only"]},
            "transfer_policy": {
                "enum": ["non_transferable", "game_internal", "cross_game_contract"]
            },
        },
        "Condition": {"expression": ref("ConditionNode")},
        "Formula": {
            "expression": ref("FormulaNode"),
            "variables": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
                "maxItems": 256,
            },
        },
        "Action": {
            "input_schema": {"type": "object"},
            "authority": {"enum": ["local", "server", "match_server"]},
            "idempotency": {"type": "string"},
            "cooldown": {},
            "conditions": {"type": "array", "items": ref("Condition")},
            "costs": {"type": "array", "items": ref("Cost")},
            "effects": {"type": "array", "items": ref("Effect")},
            "rewards": {"type": "array", "items": ref("Reward")},
            "emitted_events": {"type": "array", "items": ref("StableId")},
            "analytics": {"type": "array", "items": {"type": "string"}},
            "rate_limit_class": {"type": "string"},
        },
        "Cost": {
            "owner": ref("StableId"),
            "target": ref("Reference"),
            "quantity": ref("Formula"),
            "insufficiency": {"enum": ["reject", "partial"]},
            "ledger_reason": {"type": "string"},
        },
        "Effect": {
            "operation": {
                "enum": [
                    "set",
                    "increment",
                    "decrement",
                    "append_unique",
                    "remove",
                    "unlock",
                    "lock",
                    "grant_item",
                    "consume_item",
                    "equip",
                    "unequip",
                    "apply_modifier",
                    "remove_modifier",
                    "start_timer",
                    "cancel_timer",
                    "complete_objective",
                    "emit_event",
                ]
            },
            "path": ref("StatePath"),
            "target": ref("Reference"),
            "value": {},
        },
        "Reward": {
            "entries": {
                "type": "array",
                "items": {"type": "object"},
                "minItems": 1,
                "maxItems": 256,
            }
        },
        "Event": {
            "type": {"type": "string"},
            "major_version": {"type": "integer", "minimum": 1},
            "payload_schema": {"type": "object"},
            "producer": ref("StableId"),
            "allowed_consumers": {"type": "array", "items": ref("StableId")},
            "retention_class": {"type": "string"},
            "contains_pii": {"type": "boolean"},
            "analytics_mapping": {"type": "string"},
        },
        "Timer": {
            "timer_type": {"enum": ["one_shot", "recurring", "countdown", "cooldown", "scheduled"]},
            "authority": {"enum": ["server", "match_server", "local"]},
            "duration_formula": ref("Formula"),
            "schedule": {"type": "string"},
            "stacking_policy": {"type": "string"},
            "pause_policy": {"type": "string"},
            "on_due_action": ref("StableId"),
            "max_catch_up": {"type": "integer", "minimum": 0, "maximum": 1000},
            "offline_policy": {"type": "string"},
        },
        "Relationship": {
            "relationship_type": ref("StableId"),
            "target_type": {"type": "string"},
            "target_id": ref("StableId"),
            "metadata": ref("Metadata"),
        },
        "ProgressionNode": {
            "graph_id": ref("StableId"),
            "node_type": {"type": "string"},
            "requirements": {"type": "array", "items": ref("Condition")},
            "costs": {"type": "array", "items": ref("Cost")},
            "rewards": {"type": "array", "items": ref("Reward")},
            "effects": {"type": "array", "items": ref("Effect")},
            "dependencies": {"type": "array", "items": ref("StableId")},
            "exclusive_group": ref("StableId"),
            "repeat_policy": {"type": "string"},
            "children": {"type": "array", "items": ref("StableId")},
            "entry": {"type": "boolean"},
            "required": {"type": "boolean"},
        },
    }
    for name, fields in primitive_fields.items():
        optional_by_definition = {
            "ProgressionNode": {"entry", "required"},
            "Resource": {"route_to_resource_id", "negative_balance_approval"},
        }
        optional = optional_by_definition.get(name, set())
        definitions[name] = obj(
            {**defs["Header"]["properties"], **fields},
            list(
                dict.fromkeys(
                    [*defs["Header"]["required"], *(key for key in fields if key not in optional)]
                )
            ),
        )
    definitions["Game"] = obj(
        {
            "id": ref("StableId"),
            "studio_id": ref("StableId"),
            "name": {"type": "string", "minLength": 1, "maxLength": 128},
            "genre_labels": {"type": "array", "items": ref("Tag"), "maxItems": 32},
            "default_locale": {"type": "string"},
            "supported_locales": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "uniqueItems": True,
            },
            "blueprint": ref("StableId"),
            "network_mode": ref("NetworkMode"),
            "engine_range": {"type": "string"},
            "modules": {"type": "array", "items": ref("ReleaseLock")},
            "features": {"type": "array", "items": ref("StableId"), "uniqueItems": True},
            "state_schema_version": {"type": "string"},
            "definition_schema_version": ref("SchemaVersion"),
        }
    )
    definitions["Module"] = obj(
        {
            "id": ref("StableId"),
            "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
            "digest": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
            "engine_range": {"type": "string"},
            "requires": {"type": "array", "items": ref("Dependency")},
            "conflicts": {"type": "array", "items": ref("StableId"), "uniqueItems": True},
            "configuration": {"type": "object"},
            "state_namespaces": {"type": "array", "items": ref("StableId"), "uniqueItems": True},
            "registered_actions": {"type": "array", "items": ref("StableId")},
            "subscribed_events": {"type": "array", "items": ref("StableId")},
            "emitted_events": {"type": "array", "items": ref("StableId")},
            "registered_conditions": {"type": "array", "items": ref("StableId")},
            "registered_effects": {"type": "array", "items": ref("StableId")},
            "registered_timers": {"type": "array", "items": ref("StableId")},
            "migrations": {"type": "array", "items": {"type": "object"}},
            "resource_budget": ref("ResourceBudget"),
        }
    )
    domain_fields: dict[str, dict[str, Any]] = {
        "Item": {
            "item_type": {"type": "string"},
            "stack_limit": {"type": "integer", "minimum": 1},
            "properties": {"type": "object"},
        },
        "Inventory": {
            "owner_type": {"type": "string"},
            "slot_limit": {"type": "integer", "minimum": 0},
            "accepted_items": {"type": "array", "items": ref("StableId")},
        },
        "Quest": {
            "objectives": {"type": "array", "items": {"type": "object"}, "minItems": 1},
            "requirements": {"type": "array", "items": ref("Condition")},
            "rewards": {"type": "array", "items": ref("Reward")},
        },
        "Achievement": {
            "requirements": {"type": "array", "items": ref("Condition")},
            "rewards": {"type": "array", "items": ref("Reward")},
            "repeatable": {"type": "boolean"},
        },
        "Entitlement": {
            "grant_type": {"type": "string"},
            "scope": {"type": "string"},
            "revocable": {"type": "boolean"},
        },
        "Localization": {
            "locale": {"type": "string"},
            "entries": {
                "type": "object",
                "propertyNames": {"pattern": "^[a-z][a-z0-9_.-]{2,127}$"},
                "additionalProperties": {"type": "string", "maxLength": 4096},
            },
        },
        "LiveOps": {
            "starts_at": ref("Timestamp"),
            "ends_at": ref("Timestamp"),
            "configuration": {"type": "object"},
            "actions": {"type": "array", "items": ref("StableId")},
        },
        "Experiment": {
            "variants": {"type": "array", "items": {"type": "object"}, "minItems": 2},
            "allocation": {"type": "integer", "minimum": 0, "maximum": 10000},
            "metrics": {"type": "array", "items": {"type": "string"}},
        },
        "Analytics": {
            "event_id": ref("StableId"),
            "fields": {"type": "object"},
            "contains_pii": {"const": False},
        },
        "Save": {
            "version": {"type": "integer", "minimum": 1},
            "namespaces": {"type": "array", "items": ref("StableId")},
            "migrations": {"type": "array", "items": {"type": "object"}},
        },
        "Match": {
            "mode": {"type": "string"},
            "authority": {"enum": ["server", "match_server"]},
            "rules": {"type": "object"},
            "participants": {"type": "integer", "minimum": 1},
        },
        "CrossGameContract": {
            "source_game": ref("StableId"),
            "target_game": ref("StableId"),
            "contract_version": {"type": "string"},
            "allowed_rewards": {"type": "array", "items": ref("StableId")},
        },
    }
    for name, fields in domain_fields.items():
        definitions[name] = obj(
            {**defs["Header"]["properties"], **fields},
            list(dict.fromkeys([*defs["Header"]["required"], *fields.keys()])),
        )
    defs.update(definitions)
    document_names = list(primitive_fields) + list(domain_fields)
    defs["DefinitionBundle"] = obj(
        {
            "schema_version": ref("SchemaVersion"),
            "blueprint": ref("Blueprint"),
            "game": ref("Game"),
            "modules": {"type": "array", "items": ref("Module"), "maxItems": 128},
            "extension_manifest": ref("ExtensionManifest"),
            "documents": {
                "type": "array",
                "items": {"oneOf": [ref(name) for name in document_names]},
                "maxItems": 4096,
            },
        },
        ["schema_version", "blueprint", "game", "modules", "extension_manifest", "documents"],
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.lengeas.internal/definition/v0.1/bundle.schema.json",
        "title": "LenGeas Definition Bundle v0.1",
        "$defs": defs,
        **ref("DefinitionBundle"),
    }


def main() -> None:
    schema = catalog()
    BASE.mkdir(parents=True, exist_ok=True)
    MASTER.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    common = {
        "id": "StableId",
        "header": "Header",
        "reference": "Reference",
        "localization-key": "LocalizationKey",
        "numeric-value": "NumericValue",
        "timestamp": "Timestamp",
        "state-path": "StatePath",
    }
    groups = {
        "common": common,
        "core": {
            key.lower().replace("_", "-"): key
            for key in [
                "Game",
                "Blueprint",
                "Module",
                "Entity",
                "Resource",
                "Condition",
                "Formula",
                "Action",
                "Cost",
                "Effect",
                "Reward",
                "Event",
                "Timer",
                "Relationship",
                "ProgressionNode",
            ]
        },
        "domain": {
            key.lower().replace("_", "-"): key
            for key in [
                "Item",
                "Inventory",
                "Quest",
                "Achievement",
                "Entitlement",
                "Localization",
                "LiveOps",
                "Experiment",
                "Analytics",
                "Save",
                "Match",
                "CrossGameContract",
            ]
        },
    }
    for group, files in groups.items():
        for filename, definition in files.items():
            path = BASE / group / f"{filename}.schema.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "$schema": schema["$schema"],
                        "$id": f"{schema['$id'].rsplit('/', 1)[0]}/{group}/{filename}.schema.json",
                        "$ref": f"../bundle.schema.json#/$defs/{definition}",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    (BASE / "extension-manifest.schema.json").write_text(
        json.dumps(
            {
                "$schema": schema["$schema"],
                "$id": f"{schema['$id'].rsplit('/', 1)[0]}/extension-manifest.schema.json",
                "$ref": "bundle.schema.json#/$defs/ExtensionManifest",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
