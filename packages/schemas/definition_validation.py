"""Seven-level definition bundle validation with stable machine errors."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from packages.schemas.definition_runtime import (
    DefinitionInputError,
    canonical_bytes,
    normalize_decimal,
    parse_yaml,
    sha256_hex,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "packages/schemas/definition/v0.1/bundle.schema.json").read_text(encoding="utf-8")
)


def _error(pointer: str, code: str) -> dict[str, str]:
    return {"pointer": pointer, "code": code, "severity": "error"}


def _extension_schema_is_safe(schema: Any) -> bool:
    """Accept only valid Draft 2020-12 schemas with local-only references."""
    from jsonschema import Draft202012Validator, SchemaError  # type: ignore[import-untyped]

    pending = [schema]
    references: list[str] = []
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if key in {"$ref", "$dynamicRef", "$recursiveRef"}:
                    if not isinstance(child, str) or not child.startswith("#"):
                        return False
                    references.append(child)
                pending.append(child)
        elif isinstance(current, list):
            pending.extend(current)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError:
        return False
    for reference in references:
        if reference == "#":
            continue
        if not reference.startswith("#/"):
            return False
        target = schema
        for encoded_part in unquote(reference[2:]).split("/"):
            escape = chr(126)
            if re.search(escape + r"(?![01])", encoded_part):
                return False
            part = encoded_part.replace(escape + "1", "/").replace(escape + "0", escape)
            if not isinstance(target, dict) or part not in target:
                return False
            target = target[part]
    return True


def _version_tuple(version: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def _dependency_range_matches(version: str, version_range: str) -> bool:
    """Match the v0.1 dependency range subset: *, exact, ^M.m.p, and ~M.m.p."""
    candidate = _version_tuple(version)
    if candidate is None:
        return False
    if version_range == "*":
        return True
    match = re.fullmatch(r"([\^~]?)(.*)", version_range)
    if match is None:
        return False
    operator, requested_text = match.groups()
    requested = _version_tuple(requested_text)
    if requested is None:
        return False
    if not operator:
        return candidate == requested
    if operator == chr(126):
        upper = (requested[0], requested[1] + 1, 0)
    elif requested[0] > 0:
        upper = (requested[0] + 1, 0, 0)
    elif requested[1] > 0:
        upper = (0, requested[1] + 1, 0)
    else:
        upper = (0, 0, requested[2] + 1)
    return requested <= candidate < upper


def _dependency_range_is_valid(version_range: str) -> bool:
    if version_range == "*":
        return True
    match = re.fullmatch(r"([\^~]?)(.*)", version_range)
    return bool(match and _version_tuple(match.group(2)) is not None)


def _walk(value: Any, pointer: str = "") -> list[tuple[str, Any]]:
    result = [(pointer, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            escaped = str(key).replace(chr(126), chr(126) + "0").replace("/", chr(126) + "1")
            result.extend(_walk(child, f"{pointer}/{escaped}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_walk(child, f"{pointer}/{index}"))
    return result


def _graph_cycle(graph: dict[str, list[str]]) -> bool:
    active: set[str] = set()
    done: set[str] = set()
    for root in graph:
        if root in done:
            continue
        active.add(root)
        pending: list[tuple[str, Any]] = [(root, iter(graph.get(root, [])))]
        while pending:
            node, targets = pending[-1]
            try:
                target = next(targets)
            except StopIteration:
                pending.pop()
                active.remove(node)
                done.add(node)
                continue
            if target in active:
                return True
            if target not in done:
                active.add(target)
                pending.append((target, iter(graph.get(target, []))))
    return False


def validate_bundle(value: Any) -> dict[str, Any]:
    """Validate syntax, references, graphs, semantics, safety, runtime and simulation contracts."""
    levels: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    schema_errors = validate_document(value, SCHEMA)
    errors.extend(schema_errors)
    levels.append({"level": "syntax", "status": "failed" if schema_errors else "passed"})
    if schema_errors or not isinstance(value, dict):
        return {
            "valid": False,
            "levels": levels,
            "errors": sorted(errors, key=lambda e: (e["pointer"], e["code"])),
        }

    documents = value.get("documents", [])
    blueprint = value.get("blueprint", {})
    game = value.get("game", {})
    if game.get("blueprint") != blueprint.get("id"):
        errors.append(_error("/game/blueprint", "blueprint_reference_mismatch"))
    if game.get("network_mode") not in blueprint.get("network_modes", []):
        errors.append(_error("/game/network_mode", "blueprint_network_mode_forbidden"))
    if not set(game.get("features", [])) <= set(blueprint.get("features", [])):
        errors.append(_error("/game/features", "blueprint_feature_forbidden"))
    identifiers: dict[str, set[str]] = {
        "game": {value["game"]["id"]},
        "module": {module["id"] for module in value.get("modules", [])},
    }
    module_id_values = [module["id"] for module in value.get("modules", [])]
    if len(module_id_values) != len(set(module_id_values)):
        seen: set[str] = set()
        for index, module_id in enumerate(module_id_values):
            if module_id in seen:
                errors.append(_error(f"/modules/{index}/id", "duplicate_id"))
            seen.add(module_id)
    type_markers = {
        "entity": "entity_type",
        "resource": "resource_type",
        "condition": "expression",
        "formula": "variables",
        "action": "input_schema",
        "cost": "insufficiency",
        "effect": "operation",
        "reward": "entries",
        "event": "major_version",
        "timer": "timer_type",
        "progression_node": "graph_id",
        "item": "item_type",
        "inventory": "accepted_items",
        "quest": "objectives",
        "achievement": "repeatable",
        "entitlement": "grant_type",
        "localization": "locale",
        "experiment": "variants",
        "analytics": "event_id",
        "save": "version",
        "match": "mode",
        "cross_game_contract": "source_game",
    }
    for document in documents:
        if isinstance(document, dict) and isinstance(document.get("id"), str):
            for kind, marker in type_markers.items():
                if marker in document:
                    identifiers.setdefault(kind, set()).add(document["id"])
            if "relationship_type" in document:
                identifiers.setdefault("relationship", set()).add(document["id"])
    seen_ids: dict[str, set[str]] = {}
    for index, document in enumerate(documents):
        if not isinstance(document, dict) or not isinstance(document.get("id"), str):
            continue
        kind = next(
            (name for name, marker in type_markers.items() if marker in document),
            "relationship" if "relationship_type" in document else "unknown",
        )
        if document["id"] in seen_ids.setdefault(kind, set()):
            errors.append(_error(f"/documents/{index}/id", "duplicate_id"))
        seen_ids[kind].add(document["id"])
    registered_extensions = set(value.get("extension_manifest", {}).get("extensions", {}))
    extension_schemas = value.get("extension_manifest", {}).get("extensions", {})
    for pointer, node in _walk(documents, "/documents"):
        if isinstance(node, dict) and isinstance(node.get("extensions"), dict):
            for namespace in node["extensions"]:
                if namespace not in registered_extensions:
                    errors.append(
                        _error(f"{pointer}/extensions/{namespace}", "extension_unregistered")
                    )
                    continue
                registration = extension_schemas[namespace]
                schema = registration["schema"]
                if registration["digest"] != f"sha256:{sha256_hex(schema)}":
                    errors.append(
                        _error(
                            f"{pointer}/extensions/{namespace}", "extension_schema_digest_mismatch"
                        )
                    )
                elif not _extension_schema_is_safe(schema):
                    errors.append(
                        _error(f"{pointer}/extensions/{namespace}", "extension_schema_invalid")
                    )
                else:
                    extension_errors = validate_document(node["extensions"][namespace], schema)
                    errors.extend(
                        _error(
                            f"{pointer}/extensions/{namespace}{error['pointer']}",
                            error["code"],
                        )
                        for error in extension_errors
                    )
    locale_entries = {
        document.get("locale"): set(document.get("entries", {}))
        for document in documents
        if isinstance(document, dict) and "locale" in document
    }
    supported_locales = set(value["game"].get("supported_locales", []))
    for index, document in enumerate(documents):
        if isinstance(document, dict):
            for field in ("display_name_key", "description_key"):
                localization_key = document.get(field)
                if localization_key is not None and any(
                    localization_key not in locale_entries.get(locale, set())
                    for locale in supported_locales
                ):
                    errors.append(_error(f"/documents/{index}/{field}", "localization_key_missing"))
    for pointer, node in _walk(value):
        if isinstance(node, dict) and set(node) == {"kind", "id"}:
            targets = identifiers.get(str(node["kind"]), set())
            if node["id"] not in targets and node["kind"] not in {"game", "module"}:
                errors.append(_error(pointer, "reference_missing"))
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        typed_lists = {
            "accepted_items": "item",
            "emitted_events": "event",
        }
        for field, kind in typed_lists.items():
            for item_index, target_id in enumerate(document.get(field, [])):
                if target_id not in identifiers.get(kind, set()):
                    errors.append(
                        _error(f"/documents/{index}/{field}/{item_index}", "reference_missing")
                    )
        if "on_due_action" in document and document["on_due_action"] not in identifiers.get(
            "action", set()
        ):
            errors.append(_error(f"/documents/{index}/on_due_action", "reference_missing"))
    reference_errors = {
        "reference_missing",
        "duplicate_id",
        "extension_unregistered",
        "localization_key_missing",
        "action_owner_invalid",
        "extension_schema_digest_mismatch",
        "extension_schema_invalid",
        "schema_validation",
    }
    levels.append(
        {
            "level": "references",
            "status": "failed" if any(e["code"] in reference_errors for e in errors) else "passed",
        }
    )

    installed_module_ids = {module["id"] for module in value.get("modules", [])}
    if not set(blueprint.get("required_modules", [])) <= set(blueprint.get("allowed_modules", [])):
        errors.append(_error("/blueprint/required_modules", "required_module_not_allowed"))
    if not installed_module_ids <= set(blueprint.get("allowed_modules", [])):
        errors.append(_error("/modules", "blueprint_module_forbidden"))
    if not set(blueprint.get("required_modules", [])) <= installed_module_ids:
        errors.append(_error("/modules", "blueprint_required_module_missing"))
    module_versions = {
        module["id"]: (module["version"], module["digest"]) for module in value.get("modules", [])
    }
    graph: dict[str, list[str]] = {}
    owned_namespaces: dict[str, str] = {}
    action_owners: dict[str, list[dict[str, Any]]] = {}
    for index, module in enumerate(value.get("modules", [])):
        module_id = module["id"]
        for budget_name, budget_value in module["resource_budget"].items():
            if budget_value > blueprint["resource_budget"][budget_name]:
                errors.append(
                    _error(
                        f"/modules/{index}/resource_budget/{budget_name}",
                        "module_budget_exceeds_blueprint",
                    )
                )
        graph[module_id] = [item["module_id"] for item in module.get("requires", [])]
        if len(set(module.get("state_namespaces", []))) != len(module.get("state_namespaces", [])):
            errors.append(_error(f"/modules/{index}/state_namespaces", "duplicate_namespace"))
        for namespace in module.get("state_namespaces", []):
            if namespace in owned_namespaces and owned_namespaces[namespace] != module_id:
                errors.append(
                    _error(
                        f"/modules/{index}/state_namespaces", "namespace_owned_by_multiple_modules"
                    )
                )
            owned_namespaces[namespace] = module_id
        for action_id in module.get("registered_actions", []):
            action_owners.setdefault(action_id, []).append(module)
        if module_id in module.get("conflicts", []):
            errors.append(_error(f"/modules/{index}/conflicts", "module_self_conflict"))
        for dependency in graph[module_id]:
            if dependency not in installed_module_ids:
                errors.append(_error(f"/modules/{index}/requires", "dependency_missing"))
        for dependency_index, dependency in enumerate(module.get("requires", [])):
            dependency_id = dependency["module_id"]
            installed = next(
                (item for item in value.get("modules", []) if item["id"] == dependency_id),
                None,
            )
            range_pointer = f"/modules/{index}/requires/{dependency_index}/version_range"
            if not _dependency_range_is_valid(dependency["version_range"]):
                errors.append(_error(range_pointer, "dependency_version_range_invalid"))
            elif installed is not None and not _dependency_range_matches(
                installed["version"], dependency["version_range"]
            ):
                errors.append(_error(range_pointer, "dependency_version_mismatch"))
    if _graph_cycle(graph):
        errors.append(_error("/modules", "dependency_cycle"))
    progression: dict[str, list[str]] = {}
    progression_dependencies: dict[str, list[str]] = {}
    progression_groups: dict[str, dict[str, Any]] = {}
    progression_ids = {
        document["id"]
        for document in documents
        if isinstance(document, dict) and "graph_id" in document and "id" in document
    }
    for index, document in enumerate(documents):
        if isinstance(document, dict) and "graph_id" in document:
            child_nodes = list(document.get("children", []))
            dependency_nodes = list(document.get("dependencies", []))
            for dependency in document.get("dependencies", []):
                if dependency not in progression_ids:
                    errors.append(
                        _error(f"/documents/{index}/dependencies", "progression_target_missing")
                    )
            if any(target not in progression_ids for target in child_nodes):
                errors.append(_error(f"/documents/{index}/children", "progression_target_missing"))
            progression[document["id"]] = child_nodes
            progression_dependencies[document["id"]] = dependency_nodes
            progression_groups[document["id"]] = {
                "graph_id": document["graph_id"],
                "entry": document.get("entry", document.get("node_type") == "root"),
                "required": document.get("required", False),
            }
    if _graph_cycle(progression):
        errors.append(_error("/documents", "progression_cycle"))
    if _graph_cycle(progression_dependencies):
        errors.append(_error("/documents", "progression_dependency_cycle"))
    for graph_id in {item["graph_id"] for item in progression_groups.values()}:
        nodes = {
            node_id
            for node_id, metadata in progression_groups.items()
            if metadata["graph_id"] == graph_id
        }
        entries = {node_id for node_id in nodes if progression_groups[node_id]["entry"]}
        required_nodes = {node_id for node_id in nodes if progression_groups[node_id]["required"]}
        reachable: set[str] = set()
        pending = list(entries)
        while pending:
            node = pending.pop()
            if node not in reachable and node in nodes:
                reachable.add(node)
                pending.extend(progression.get(node, []))
        if not required_nodes <= reachable:
            errors.append(_error("/documents", "progression_unreachable"))
    reward_graph: dict[str, list[str]] = {}
    for document in documents:
        if (
            isinstance(document, dict)
            and "entries" in document
            and isinstance(document["entries"], list)
        ):
            reward_graph[document["id"]] = [
                node["id"]
                for pointer, node in _walk(document["entries"])
                if isinstance(node, dict)
                and node.get("kind") == "reward"
                and isinstance(node.get("id"), str)
            ]
    if _graph_cycle(reward_graph):
        errors.append(_error("/documents", "reward_loop"))
    for left, module in enumerate(value.get("modules", [])):
        if set(module.get("conflicts", [])) & installed_module_ids:
            errors.append(_error(f"/modules/{left}/conflicts", "module_conflict_installed"))
    for index, document in enumerate(documents):
        if isinstance(document, dict) and "input_schema" in document:
            if len(action_owners.get(document["id"], [])) != 1:
                errors.append(_error(f"/documents/{index}/id", "action_owner_invalid"))
        if isinstance(document, dict) and "operation" in document and "path" in document:
            owners = [
                module
                for module in value["modules"]
                if document["id"] in module.get("registered_effects", [])
            ]
            if len(owners) != 1:
                errors.append(_error(f"/documents/{index}/id", "effect_owner_invalid"))
            elif document["path"]["namespace_id"] not in owners[0]["state_namespaces"]:
                errors.append(
                    _error(f"/documents/{index}/path/namespace_id", "namespace_violation")
                )
    locks = {
        lock["module_id"]: (lock["version"], lock["digest"])
        for lock in value["game"].get("modules", [])
    }
    if locks != module_versions:
        errors.append(_error("/game/modules", "release_lock_mismatch"))
    module_order = [module["id"] for module in value.get("modules", [])]
    if module_order != sorted(module_order):
        errors.append(_error("/modules", "canonical_order"))
    document_order = [(doc["id"], canonical_bytes(doc)) for doc in documents]
    if document_order != sorted(document_order):
        errors.append(_error("/documents", "canonical_order"))
    levels.append(
        {
            "level": "graph",
            "status": "failed"
            if any(
                e["code"]
                in {
                    "dependency_missing",
                    "dependency_cycle",
                    "dependency_version_mismatch",
                    "dependency_version_range_invalid",
                    "module_self_conflict",
                    "module_conflict_installed",
                    "effect_owner_invalid",
                    "duplicate_namespace",
                    "release_lock_mismatch",
                    "canonical_order",
                    "progression_target_missing",
                    "progression_cycle",
                    "progression_dependency_cycle",
                    "progression_unreachable",
                    "reward_loop",
                    "namespace_owned_by_multiple_modules",
                    "namespace_violation",
                }
                for e in errors
            )
            else "passed",
        }
    )

    network_mode = value.get("game", {}).get("network_mode")
    for index, document in enumerate(documents):
        if isinstance(document, dict) and document.get("tags", []) != sorted(
            document.get("tags", [])
        ):
            errors.append(_error(f"/documents/{index}/tags", "canonical_order"))
        if (
            isinstance(document, dict)
            and document.get("authority") == "local"
            and network_mode == "server_authoritative"
        ):
            errors.append(_error(f"/documents/{index}/authority", "authority_mode_conflict"))
        if (
            isinstance(document, dict)
            and document.get("minimum") is not None
            and document.get("maximum") is not None
        ):
            try:
                if Decimal(str(document["minimum"])) > Decimal(str(document["maximum"])):
                    errors.append(_error(f"/documents/{index}/minimum", "impossible_range"))
            except (InvalidOperation, TypeError, ValueError):
                errors.append(_error(f"/documents/{index}/minimum", "numeric_value_invalid"))
        if isinstance(document, dict):
            for field in ("initial_amount", "minimum", "maximum"):
                numeric = document.get(field)
                if isinstance(numeric, str) and re.fullmatch(r"-?[0-9].*", numeric):
                    try:
                        normalize_decimal(numeric)
                    except DefinitionInputError as error:
                        errors.append(_error(f"/documents/{index}/{field}", error.code))
            if "numeric_model" in document:
                minimum = Decimal(str(document["minimum"]))
                maximum = Decimal(str(document["maximum"]))
                initial = Decimal(str(document["initial_amount"]))
                if initial < minimum or initial > maximum:
                    errors.append(
                        _error(f"/documents/{index}/initial_amount", "initial_amount_out_of_range")
                    )
                model = document["numeric_model"]
                if model["type"] == "integer" and any(
                    value != value.to_integral_value() for value in (minimum, maximum, initial)
                ):
                    errors.append(
                        _error(
                            f"/documents/{index}/numeric_model", "numeric_model_precision_mismatch"
                        )
                    )
                if model["type"] == "fixed_decimal":
                    scale = model["scale"]
                    for field in ("initial_amount", "minimum", "maximum"):
                        raw_value = document[field]
                        exponent = Decimal(str(raw_value)).as_tuple().exponent
                        actual_scale = max(0, -exponent) if isinstance(exponent, int) else scale + 1
                        if actual_scale > scale:
                            errors.append(
                                _error(
                                    f"/documents/{index}/{field}",
                                    "numeric_model_precision_mismatch",
                                )
                            )
                if document.get("overflow_policy") == "route_to_resource" and not document.get(
                    "route_to_resource_id"
                ):
                    errors.append(
                        _error(f"/documents/{index}/route_to_resource_id", "overflow_route_missing")
                    )
                if minimum < 0:
                    approval = document.get("negative_balance_approval")
                    unsigned = {
                        key: item
                        for key, item in document.items()
                        if key != "negative_balance_approval"
                    }
                    if (
                        not isinstance(approval, dict)
                        or approval.get("reviewer_role") != "security_owner"
                        or approval.get("approved") is not True
                        or approval.get("resource_digest") != f"sha256:{sha256_hex(unsigned)}"
                    ):
                        errors.append(
                            _error(
                                f"/documents/{index}/negative_balance_approval",
                                "negative_balance_approval_required",
                            )
                        )
    levels.append(
        {
            "level": "semantic",
            "status": "failed"
            if any(
                e["code"]
                in {
                    "authority_mode_conflict",
                    "impossible_range",
                    "numeric_value_invalid",
                    "blueprint_reference_mismatch",
                    "blueprint_network_mode_forbidden",
                    "blueprint_feature_forbidden",
                    "blueprint_module_forbidden",
                    "blueprint_required_module_missing",
                    "required_module_not_allowed",
                    "module_budget_exceeds_blueprint",
                    "initial_amount_out_of_range",
                    "numeric_model_precision_mismatch",
                    "overflow_route_missing",
                    "negative_balance_approval_required",
                }
                for e in errors
            )
            else "passed",
        }
    )

    for pointer, node in _walk(value):
        if isinstance(node, dict):
            if node.get("contains_pii") is True and node.get("analytics_mapping"):
                errors.append(_error(pointer, "pii_analytics_forbidden"))
            if any(
                key in node
                for key in ("network_url", "script", "code", "system_call", "reflection")
            ):
                errors.append(_error(pointer, "unsafe_dynamic_configuration"))
            if node.get("operator") == "divide" and len(node.get("args", [])) > 1:
                denominator = node["args"][1]
                if isinstance(denominator, dict) and denominator.get("operator") == "literal":
                    denominator = denominator.get("value")
                try:
                    is_zero = Decimal(str(denominator)) == 0
                except (InvalidOperation, TypeError, ValueError):
                    is_zero = False
                if is_zero:
                    errors.append(_error(pointer, "division_by_zero"))
            if "configuration" in node:
                forbidden = {
                    "authority",
                    "transfer_policy",
                    "entitlement",
                    "price",
                    "reward",
                    "permissions",
                }
                if forbidden & set(node.get("configuration", {})):
                    errors.append(
                        _error(f"{pointer}/configuration", "remote_config_forbidden_field")
                    )
    blueprint_budget = value["blueprint"]["resource_budget"]
    operation_budget = min(
        [
            blueprint_budget["max_formula_operations"],
            *(module["resource_budget"]["max_formula_operations"] for module in value["modules"]),
        ]
    )
    condition_budget = min(
        [
            blueprint_budget["max_condition_nodes"],
            *(module["resource_budget"]["max_condition_nodes"] for module in value["modules"]),
        ]
    )
    depth_limit = min(
        [
            blueprint_budget["max_ast_depth"],
            *(module["resource_budget"]["max_ast_depth"] for module in value["modules"]),
        ]
    )

    formula_prefixes: dict[str, set[str]] = {}
    condition_prefixes: set[str] = set()
    for pointer, node in _walk(value):
        if isinstance(node, dict) and "expression" in node:
            expression_pointer = f"{pointer}/expression"
            if "variables" in node:
                formula_prefixes[expression_pointer] = set(node.get("variables", []))
            else:
                condition_prefixes.add(expression_pointer)

    def ast_metrics(node: Any) -> tuple[int, int]:
        """Count every operator in nested AST branches, including piecewise cases."""
        count = 0
        max_depth = 0
        pending: list[tuple[Any, int]] = [(node, 0)]
        while pending:
            current, depth = pending.pop()
            if isinstance(current, dict):
                if "operator" in current:
                    count += 1
                    max_depth = max(max_depth, depth)
                    child_depth = depth + 1
                else:
                    child_depth = depth
                pending.extend((child, child_depth) for child in current.values())
            elif isinstance(current, list):
                pending.extend((child, depth) for child in current)
        return count, max_depth

    def enclosing_prefix(pointer: str, prefixes: Any) -> str | None:
        return next(
            (
                prefix
                for prefix in prefixes
                if pointer == prefix or pointer.startswith(prefix + "/")
            ),
            None,
        )

    ast_roots = sorted(
        [(prefix, True) for prefix in formula_prefixes]
        + [(prefix, False) for prefix in condition_prefixes]
    )
    for prefix, is_formula in ast_roots:
        ast_root: Any = value
        for part in prefix.strip("/").split("/"):
            ast_root = ast_root[int(part)] if isinstance(ast_root, list) else ast_root[part]
        size, depth = ast_metrics(ast_root)
        budget = operation_budget if is_formula else condition_budget
        if size > budget or depth > depth_limit:
            errors.append(
                _error(
                    prefix,
                    "formula_operation_budget_exceeded"
                    if is_formula
                    else "condition_budget_exceeded",
                )
            )

    for pointer, node in _walk(value):
        if isinstance(node, dict) and "operator" in node:
            formula_prefix = enclosing_prefix(pointer, formula_prefixes)
            if node.get("operator") == "variable" and formula_prefix is not None:
                if node.get("name") not in formula_prefixes[formula_prefix]:
                    errors.append(_error(f"{pointer}/name", "formula_variable_not_allowed"))
            if node.get("operator") == "literal" and isinstance(node.get("value"), str):
                try:
                    normalize_decimal(node["value"])
                except DefinitionInputError as error:
                    errors.append(_error(f"{pointer}/value", error.code))
            if node.get("operator") == "power_integer":
                exponent = node.get("args", [None, None])[1]
                if (
                    not isinstance(exponent, dict)
                    or exponent.get("operator") != "literal"
                    or not isinstance(exponent.get("value"), int)
                    or not -16 <= exponent["value"] <= 16
                ):
                    errors.append(_error(f"{pointer}/args/1", "formula_exponent_invalid"))
    levels.append(
        {
            "level": "safety",
            "status": "failed"
            if any(
                e["code"]
                in {
                    "pii_analytics_forbidden",
                    "unsafe_dynamic_configuration",
                    "division_by_zero",
                    "remote_config_forbidden_field",
                    "formula_operation_budget_exceeded",
                    "condition_budget_exceeded",
                    "numeric_scale_exceeded",
                    "numeric_overflow",
                    "decimal_not_normalized",
                    "formula_variable_not_allowed",
                    "formula_exponent_invalid",
                }
                for e in errors
            )
            else "passed",
        }
    )
    levels.append(
        {
            "level": "runtime",
            "status": "conformance_only",
            "evidence": "schema loading conformance only; runtime execution is not implemented",
        }
    )
    levels.append(
        {
            "level": "simulation",
            "status": "conformance_only",
            "evidence": "no balance simulator or simulation invariant suite is implemented",
        }
    )
    if any(error["code"] == "action_owner_invalid" for error in errors):
        levels[1]["status"] = "failed"
    return {
        "valid": not errors,
        "staging_eligible": False,
        "levels": levels,
        "errors": sorted(errors, key=lambda e: (e["pointer"], e["code"])),
    }


def validate_yaml(text: str) -> dict[str, Any]:
    try:
        return validate_bundle(parse_yaml(text))
    except DefinitionInputError as error:
        return {
            "valid": False,
            "levels": [{"level": "syntax", "status": "failed"}],
            "errors": [error.as_dict()],
        }
