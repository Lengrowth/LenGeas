"""Generated definition v0.1 model shapes. Do not edit."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, Required, TypedDict

StableId = str
SchemaVersion = Literal["0.1.0"]
LocalizationKey = str
Tag = str
Tags = list[Tag]
Metadata = dict[str, Any]
Extensions = dict[str, Any]
Timestamp = str
CanonicalDecimal = str
IntegerValue = int
NumericValue = IntegerValue | CanonicalDecimal
NumericModel = dict[str, Any]
ReferenceKind = Literal[
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
FormulaOperand = int | str | bool | None | dict[str, Any]
FormulaNode = dict[str, Any]
ConditionNode = dict[str, Any]
NetworkMode = Literal[
    "offline", "offline_first", "online_optional", "online_required", "server_authoritative"
]


class Header(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]


class Reference(TypedDict, total=False):
    kind: Required[ReferenceKind]
    id: Required[StableId]


class StatePath(TypedDict, total=False):
    namespace_id: Required[StableId]
    segments: Required[list[str]]


class Dependency(TypedDict, total=False):
    module_id: Required[StableId]
    version_range: Required[str]


class ReleaseLock(TypedDict, total=False):
    module_id: Required[StableId]
    version: Required[str]
    digest: Required[str]


class Blueprint(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    studio_id: Required[StableId]
    name: Required[str]
    network_modes: Required[list[NetworkMode]]
    features: Required[list[StableId]]
    allowed_modules: Required[list[StableId]]
    required_modules: Required[list[StableId]]
    resource_budget: Required[ResourceBudget]


class ResourceBudget(TypedDict, total=False):
    max_formula_operations: Required[int]
    max_condition_nodes: Required[int]
    max_ast_depth: Required[int]
    max_events_per_action: Required[int]


class ExtensionRegistration(TypedDict, total=False):
    schema_id: Required[str]
    digest: Required[str]
    schema: Required[dict[str, Any]]


class ExtensionManifest(TypedDict, total=False):
    schema_version: Required[SchemaVersion]
    extensions: Required[dict[str, Any]]


class PackageManifest(TypedDict, total=False):
    schema_version: Required[SchemaVersion]
    game: Required[str]
    blueprint: Required[str]
    modules: Required[list[str]]
    extension_manifest: Required[str]
    documents: Required[list[str]]


class Entity(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    entity_type: Required[str]
    initial_state: Required[dict[str, Any]]
    properties: Required[dict[str, Any]]
    relationships: Required[list[dict[str, Any]]]


class Resource(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    resource_type: Required[str]
    numeric_model: Required[NumericModel]
    initial_amount: Required[NumericValue]
    minimum: Required[NumericValue]
    maximum: Required[NumericValue]
    overflow_policy: Required[Literal["reject", "clamp", "route_to_resource"]]
    route_to_resource_id: NotRequired[StableId]
    negative_balance_approval: NotRequired[dict[str, Any]]
    visibility: Required[Literal["public", "private", "server_only"]]
    transfer_policy: Required[Literal["non_transferable", "game_internal", "cross_game_contract"]]


class Condition(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    expression: Required[ConditionNode]


class Formula(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    expression: Required[FormulaNode]
    variables: Required[list[str]]


class Action(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    input_schema: Required[dict[str, Any]]
    authority: Required[Literal["local", "server", "match_server"]]
    idempotency: Required[str]
    cooldown: Required[Any]
    conditions: Required[list[Condition]]
    costs: Required[list[Cost]]
    effects: Required[list[Effect]]
    rewards: Required[list[Reward]]
    emitted_events: Required[list[StableId]]
    analytics: Required[list[str]]
    rate_limit_class: Required[str]


class Cost(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    owner: Required[StableId]
    target: Required[Reference]
    quantity: Required[Formula]
    insufficiency: Required[Literal["reject", "partial"]]
    ledger_reason: Required[str]


class Effect(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    operation: Required[
        Literal[
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
    ]
    path: Required[StatePath]
    target: Required[Reference]
    value: Required[Any]


class Reward(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    entries: Required[list[dict[str, Any]]]


class Event(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    type: Required[str]
    major_version: Required[int]
    payload_schema: Required[dict[str, Any]]
    producer: Required[StableId]
    allowed_consumers: Required[list[StableId]]
    retention_class: Required[str]
    contains_pii: Required[bool]
    analytics_mapping: Required[str]


class Timer(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    timer_type: Required[Literal["one_shot", "recurring", "countdown", "cooldown", "scheduled"]]
    authority: Required[Literal["server", "match_server", "local"]]
    duration_formula: Required[Formula]
    schedule: Required[str]
    stacking_policy: Required[str]
    pause_policy: Required[str]
    on_due_action: Required[StableId]
    max_catch_up: Required[int]
    offline_policy: Required[str]


class Relationship(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    relationship_type: Required[StableId]
    target_type: Required[str]
    target_id: Required[StableId]


class ProgressionNode(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    graph_id: Required[StableId]
    node_type: Required[str]
    requirements: Required[list[Condition]]
    costs: Required[list[Cost]]
    rewards: Required[list[Reward]]
    effects: Required[list[Effect]]
    dependencies: Required[list[StableId]]
    exclusive_group: Required[StableId]
    repeat_policy: Required[str]
    children: Required[list[StableId]]
    entry: NotRequired[bool]
    required: NotRequired[bool]


class Game(TypedDict, total=False):
    id: Required[StableId]
    studio_id: Required[StableId]
    name: Required[str]
    genre_labels: Required[list[Tag]]
    default_locale: Required[str]
    supported_locales: Required[list[str]]
    blueprint: Required[StableId]
    network_mode: Required[NetworkMode]
    engine_range: Required[str]
    modules: Required[list[ReleaseLock]]
    features: Required[list[StableId]]
    state_schema_version: Required[str]
    definition_schema_version: Required[SchemaVersion]


class Module(TypedDict, total=False):
    id: Required[StableId]
    version: Required[str]
    digest: Required[str]
    engine_range: Required[str]
    requires: Required[list[Dependency]]
    conflicts: Required[list[StableId]]
    configuration: Required[dict[str, Any]]
    state_namespaces: Required[list[StableId]]
    registered_actions: Required[list[StableId]]
    subscribed_events: Required[list[StableId]]
    emitted_events: Required[list[StableId]]
    registered_conditions: Required[list[StableId]]
    registered_effects: Required[list[StableId]]
    registered_timers: Required[list[StableId]]
    migrations: Required[list[dict[str, Any]]]
    resource_budget: Required[ResourceBudget]


class Item(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    item_type: Required[str]
    stack_limit: Required[int]
    properties: Required[dict[str, Any]]


class Inventory(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    owner_type: Required[str]
    slot_limit: Required[int]
    accepted_items: Required[list[StableId]]


class Quest(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    objectives: Required[list[dict[str, Any]]]
    requirements: Required[list[Condition]]
    rewards: Required[list[Reward]]


class Achievement(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    requirements: Required[list[Condition]]
    rewards: Required[list[Reward]]
    repeatable: Required[bool]


class Entitlement(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    grant_type: Required[str]
    scope: Required[str]
    revocable: Required[bool]


class Localization(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    locale: Required[str]
    entries: Required[dict[str, Any]]


class LiveOps(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    starts_at: Required[Timestamp]
    ends_at: Required[Timestamp]
    configuration: Required[dict[str, Any]]
    actions: Required[list[StableId]]


class Experiment(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    variants: Required[list[dict[str, Any]]]
    allocation: Required[int]
    metrics: Required[list[str]]


class Analytics(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    event_id: Required[StableId]
    fields: Required[dict[str, Any]]
    contains_pii: Required[Literal[False]]


class Save(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    version: Required[int]
    namespaces: Required[list[StableId]]
    migrations: Required[list[dict[str, Any]]]


class Match(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    mode: Required[str]
    authority: Required[Literal["server", "match_server"]]
    rules: Required[dict[str, Any]]
    participants: Required[int]


class CrossGameContract(TypedDict, total=False):
    id: Required[StableId]
    schema_version: Required[SchemaVersion]
    display_name_key: NotRequired[LocalizationKey]
    description_key: NotRequired[LocalizationKey]
    tags: Required[Tags]
    enabled: Required[bool]
    metadata: Required[Metadata]
    extensions: Required[Extensions]
    source_game: Required[StableId]
    target_game: Required[StableId]
    contract_version: Required[str]
    allowed_rewards: Required[list[StableId]]


class DefinitionBundle(TypedDict, total=False):
    schema_version: Required[SchemaVersion]
    blueprint: Required[Blueprint]
    game: Required[Game]
    modules: Required[list[Module]]
    extension_manifest: Required[ExtensionManifest]
    documents: Required[
        list[
            Entity
            | Resource
            | Condition
            | Formula
            | Action
            | Cost
            | Effect
            | Reward
            | Event
            | Timer
            | Relationship
            | ProgressionNode
            | Item
            | Inventory
            | Quest
            | Achievement
            | Entitlement
            | Localization
            | LiveOps
            | Experiment
            | Analytics
            | Save
            | Match
            | CrossGameContract
        ]
    ]


SCHEMA_VERSION = "0.1.0"
