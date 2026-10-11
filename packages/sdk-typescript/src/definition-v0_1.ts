// Generated from packages/schemas/definition/v0.1/bundle.schema.json. Do not edit.
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

export type StableId = string;
export type SchemaVersion = "0.1.0";
export type LocalizationKey = string;
export type Tag = string;
export type Tags = Tag[];
export type Metadata = Record<string, unknown>;
export type Extensions = Record<string, unknown>;
export type Timestamp = string;
export type CanonicalDecimal = string;
export type IntegerValue = number;
export type NumericValue = IntegerValue | CanonicalDecimal;
export type NumericModel = Record<string, unknown>;
export type ReferenceKind =
  | "game"
  | "module"
  | "entity"
  | "resource"
  | "condition"
  | "formula"
  | "action"
  | "cost"
  | "effect"
  | "reward"
  | "event"
  | "timer"
  | "relationship"
  | "progression_node"
  | "item"
  | "quest"
  | "achievement"
  | "entitlement"
  | "localization"
  | "experiment"
  | "save"
  | "match"
  | "cross_game_contract";
export type FormulaOperand =
  | number
  | string
  | boolean
  | null
  | Record<string, unknown>;
export type FormulaNode = Record<string, unknown>;
export type ConditionNode = Record<string, unknown>;
export type NetworkMode =
  | "offline"
  | "offline_first"
  | "online_optional"
  | "online_required"
  | "server_authoritative";

export interface Header {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
}

export interface Reference {
  kind: ReferenceKind;
  id: StableId;
}

export interface StatePath {
  namespace_id: StableId;
  segments: string[];
}

export interface Dependency {
  module_id: StableId;
  version_range: string;
}

export interface ReleaseLock {
  module_id: StableId;
  version: string;
  digest: string;
}

export interface Blueprint {
  id: StableId;
  schema_version: SchemaVersion;
  studio_id: StableId;
  name: string;
  network_modes: NetworkMode[];
  features: StableId[];
  allowed_modules: StableId[];
  required_modules: StableId[];
  resource_budget: ResourceBudget;
}

export interface ResourceBudget {
  max_formula_operations: number;
  max_condition_nodes: number;
  max_ast_depth: number;
  max_events_per_action: number;
}

export interface ExtensionRegistration {
  schema_id: string;
  digest: string;
  schema: Record<string, unknown>;
}

export interface ExtensionManifest {
  schema_version: SchemaVersion;
  extensions: Record<string, unknown>;
}

export interface PackageManifest {
  schema_version: SchemaVersion;
  game: string;
  blueprint: string;
  modules: string[];
  extension_manifest: string;
  documents: string[];
}

export interface Entity {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  entity_type: string;
  initial_state: Record<string, unknown>;
  properties: Record<string, unknown>;
  relationships: Record<string, unknown>[];
}

export interface Resource {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  resource_type: string;
  numeric_model: NumericModel;
  initial_amount: NumericValue;
  minimum: NumericValue;
  maximum: NumericValue;
  overflow_policy: "reject" | "clamp" | "route_to_resource";
  route_to_resource_id?: StableId;
  negative_balance_approval?: Record<string, unknown>;
  visibility: "public" | "private" | "server_only";
  transfer_policy: "non_transferable" | "game_internal" | "cross_game_contract";
}

export interface Condition {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  expression: ConditionNode;
}

export interface Formula {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  expression: FormulaNode;
  variables: string[];
}

export interface Action {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  input_schema: Record<string, unknown>;
  authority: "local" | "server" | "match_server";
  idempotency: string;
  cooldown: unknown;
  conditions: Condition[];
  costs: Cost[];
  effects: Effect[];
  rewards: Reward[];
  emitted_events: StableId[];
  analytics: string[];
  rate_limit_class: string;
}

export interface Cost {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  owner: StableId;
  target: Reference;
  quantity: Formula;
  insufficiency: "reject" | "partial";
  ledger_reason: string;
}

export interface Effect {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  operation:
    | "set"
    | "increment"
    | "decrement"
    | "append_unique"
    | "remove"
    | "unlock"
    | "lock"
    | "grant_item"
    | "consume_item"
    | "equip"
    | "unequip"
    | "apply_modifier"
    | "remove_modifier"
    | "start_timer"
    | "cancel_timer"
    | "complete_objective"
    | "emit_event";
  path: StatePath;
  target: Reference;
  value: unknown;
}

export interface Reward {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  entries: Record<string, unknown>[];
}

export interface Event {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  type: string;
  major_version: number;
  payload_schema: Record<string, unknown>;
  producer: StableId;
  allowed_consumers: StableId[];
  retention_class: string;
  contains_pii: boolean;
  analytics_mapping: string;
}

export interface Timer {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  timer_type: "one_shot" | "recurring" | "countdown" | "cooldown" | "scheduled";
  authority: "server" | "match_server" | "local";
  duration_formula: Formula;
  schedule: string;
  stacking_policy: string;
  pause_policy: string;
  on_due_action: StableId;
  max_catch_up: number;
  offline_policy: string;
}

export interface Relationship {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  relationship_type: StableId;
  target_type: string;
  target_id: StableId;
}

export interface ProgressionNode {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  graph_id: StableId;
  node_type: string;
  requirements: Condition[];
  costs: Cost[];
  rewards: Reward[];
  effects: Effect[];
  dependencies: StableId[];
  exclusive_group: StableId;
  repeat_policy: string;
  children: StableId[];
  entry?: boolean;
  required?: boolean;
}

export interface Game {
  id: StableId;
  studio_id: StableId;
  name: string;
  genre_labels: Tag[];
  default_locale: string;
  supported_locales: string[];
  blueprint: StableId;
  network_mode: NetworkMode;
  engine_range: string;
  modules: ReleaseLock[];
  features: StableId[];
  state_schema_version: string;
  definition_schema_version: SchemaVersion;
}

export interface Module {
  id: StableId;
  version: string;
  digest: string;
  engine_range: string;
  requires: Dependency[];
  conflicts: StableId[];
  configuration: Record<string, unknown>;
  state_namespaces: StableId[];
  registered_actions: StableId[];
  subscribed_events: StableId[];
  emitted_events: StableId[];
  registered_conditions: StableId[];
  registered_effects: StableId[];
  registered_timers: StableId[];
  migrations: Record<string, unknown>[];
  resource_budget: ResourceBudget;
}

export interface Item {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  item_type: string;
  stack_limit: number;
  properties: Record<string, unknown>;
}

export interface Inventory {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  owner_type: string;
  slot_limit: number;
  accepted_items: StableId[];
}

export interface Quest {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  objectives: Record<string, unknown>[];
  requirements: Condition[];
  rewards: Reward[];
}

export interface Achievement {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  requirements: Condition[];
  rewards: Reward[];
  repeatable: boolean;
}

export interface Entitlement {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  grant_type: string;
  scope: string;
  revocable: boolean;
}

export interface Localization {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  locale: string;
  entries: Record<string, unknown>;
}

export interface LiveOps {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  starts_at: Timestamp;
  ends_at: Timestamp;
  configuration: Record<string, unknown>;
  actions: StableId[];
}

export interface Experiment {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  variants: Record<string, unknown>[];
  allocation: number;
  metrics: string[];
}

export interface Analytics {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  event_id: StableId;
  fields: Record<string, unknown>;
  contains_pii: false;
}

export interface Save {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  version: number;
  namespaces: StableId[];
  migrations: Record<string, unknown>[];
}

export interface Match {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  mode: string;
  authority: "server" | "match_server";
  rules: Record<string, unknown>;
  participants: number;
}

export interface CrossGameContract {
  id: StableId;
  schema_version: SchemaVersion;
  display_name_key?: LocalizationKey;
  description_key?: LocalizationKey;
  tags: Tags;
  enabled: boolean;
  metadata: Metadata;
  extensions: Extensions;
  source_game: StableId;
  target_game: StableId;
  contract_version: string;
  allowed_rewards: StableId[];
}

export interface DefinitionBundle {
  schema_version: SchemaVersion;
  blueprint: Blueprint;
  game: Game;
  modules: Module[];
  extension_manifest: ExtensionManifest;
  documents:
    | Entity
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
    | CrossGameContract[];
}

export interface DefinitionTypeMap {
  StableId: StableId;
  SchemaVersion: SchemaVersion;
  LocalizationKey: LocalizationKey;
  Tag: Tag;
  Tags: Tags;
  Metadata: Metadata;
  Extensions: Extensions;
  Header: Header;
  Timestamp: Timestamp;
  CanonicalDecimal: CanonicalDecimal;
  IntegerValue: IntegerValue;
  NumericValue: NumericValue;
  NumericModel: NumericModel;
  ReferenceKind: ReferenceKind;
  Reference: Reference;
  StatePath: StatePath;
  FormulaOperand: FormulaOperand;
  FormulaNode: FormulaNode;
  ConditionNode: ConditionNode;
  NetworkMode: NetworkMode;
  Dependency: Dependency;
  ReleaseLock: ReleaseLock;
  Blueprint: Blueprint;
  ResourceBudget: ResourceBudget;
  ExtensionRegistration: ExtensionRegistration;
  ExtensionManifest: ExtensionManifest;
  PackageManifest: PackageManifest;
  Entity: Entity;
  Resource: Resource;
  Condition: Condition;
  Formula: Formula;
  Action: Action;
  Cost: Cost;
  Effect: Effect;
  Reward: Reward;
  Event: Event;
  Timer: Timer;
  Relationship: Relationship;
  ProgressionNode: ProgressionNode;
  Game: Game;
  Module: Module;
  Item: Item;
  Inventory: Inventory;
  Quest: Quest;
  Achievement: Achievement;
  Entitlement: Entitlement;
  Localization: Localization;
  LiveOps: LiveOps;
  Experiment: Experiment;
  Analytics: Analytics;
  Save: Save;
  Match: Match;
  CrossGameContract: CrossGameContract;
  DefinitionBundle: DefinitionBundle;
}

export const definitionSchemaNames = [
  "StableId",
  "SchemaVersion",
  "LocalizationKey",
  "Tag",
  "Tags",
  "Metadata",
  "Extensions",
  "Header",
  "Timestamp",
  "CanonicalDecimal",
  "IntegerValue",
  "NumericValue",
  "NumericModel",
  "ReferenceKind",
  "Reference",
  "StatePath",
  "FormulaOperand",
  "FormulaNode",
  "ConditionNode",
  "NetworkMode",
  "Dependency",
  "ReleaseLock",
  "Blueprint",
  "ResourceBudget",
  "ExtensionRegistration",
  "ExtensionManifest",
  "PackageManifest",
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
  "Game",
  "Module",
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
  "DefinitionBundle",
] as const satisfies readonly (keyof DefinitionTypeMap)[];

export type DefinitionSchemaName = (typeof definitionSchemaNames)[number];

export interface DefinitionValidationError {
  pointer: string;
  code: "schema_validation";
  severity: "error";
}

export type DefinitionValidationResult<T = unknown> =
  | { valid: true; value: T; errors: [] }
  | { valid: false; errors: DefinitionValidationError[] };

const DEFINITION_SCHEMA_V0_1 = JSON.parse(
  '{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://schemas.lengeas.internal/definition/v0.1/bundle.schema.json","title":"LenGeas Definition Bundle v0.1","$defs":{"StableId":{"type":"string","pattern":"^[a-z][a-z0-9_]{2,63}$","maxLength":64},"SchemaVersion":{"type":"string","const":"0.1.0"},"LocalizationKey":{"type":"string","pattern":"^[a-z][a-z0-9_.-]{2,127}$","maxLength":128},"Tag":{"type":"string","pattern":"^[a-z0-9][a-z0-9_.-]{0,63}$","maxLength":64},"Tags":{"type":"array","items":{"$ref":"#/$defs/Tag"},"uniqueItems":true,"maxItems":32},"Metadata":{"type":"object","propertyNames":{"pattern":"^[a-z][a-z0-9_]{0,63}$"},"additionalProperties":{"type":"string","maxLength":256},"maxProperties":128},"Extensions":{"type":"object","propertyNames":{"pattern":"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$"},"additionalProperties":true,"maxProperties":64},"Header":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"}},"required":["id","schema_version","tags","enabled","metadata","extensions"],"additionalProperties":false},"Timestamp":{"type":"string","format":"date-time","pattern":"^\\\\d{4}-\\\\d{2}-\\\\d{2}T\\\\d{2}:\\\\d{2}:\\\\d{2}(?:\\\\.\\\\d{1,6})?Z$","maxLength":27},"CanonicalDecimal":{"type":"string","pattern":"^-?(?:0|[1-9][0-9]*)(?:\\\\.[0-9]*[1-9])?$","maxLength":32},"IntegerValue":{"type":"integer","minimum":-9223372036854775808,"maximum":9223372036854775807},"NumericValue":{"oneOf":[{"$ref":"#/$defs/IntegerValue"},{"$ref":"#/$defs/CanonicalDecimal"}]},"NumericModel":{"oneOf":[{"type":"object","properties":{"type":{"const":"integer"}},"required":["type"],"additionalProperties":false},{"type":"object","properties":{"type":{"const":"fixed_decimal"},"scale":{"type":"integer","minimum":0,"maximum":9}},"required":["type","scale"],"additionalProperties":false}]},"ReferenceKind":{"enum":["game","module","entity","resource","condition","formula","action","cost","effect","reward","event","timer","relationship","progression_node","item","quest","achievement","entitlement","localization","experiment","save","match","cross_game_contract"]},"Reference":{"type":"object","properties":{"kind":{"$ref":"#/$defs/ReferenceKind"},"id":{"$ref":"#/$defs/StableId"}},"required":["kind","id"],"additionalProperties":false},"StatePath":{"type":"object","properties":{"namespace_id":{"$ref":"#/$defs/StableId"},"segments":{"type":"array","items":{"type":"string","pattern":"^[a-z][a-z0-9_]{0,63}$"},"minItems":1,"maxItems":32}},"required":["namespace_id","segments"],"additionalProperties":false},"FormulaOperand":{"oneOf":[{"type":"integer"},{"type":"string","maxLength":4096},{"type":"boolean"},{"type":"null"},{"type":"object","properties":{"path":{"$ref":"#/$defs/StatePath"}},"required":["path"],"additionalProperties":false}]},"FormulaNode":{"oneOf":[{"type":"object","properties":{"operator":{"const":"literal"},"value":{"$ref":"#/$defs/NumericValue"}},"required":["operator","value"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"variable"},"name":{"type":"string","minLength":1,"maxLength":128}},"required":["operator","name"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"add"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"subtract"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"multiply"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"divide"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"min"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"max"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"clamp"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":3,"maxItems":3}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"floor"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":1,"maxItems":1}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"ceil"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":1,"maxItems":1}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"power_integer"},"args":{"type":"array","items":{"$ref":"#/$defs/FormulaNode"},"minItems":2,"maxItems":2}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"piecewise"},"cases":{"type":"array","items":{"type":"object","properties":{"when":{"$ref":"#/$defs/ConditionNode"},"then":{"$ref":"#/$defs/FormulaNode"}},"required":["when","then"],"additionalProperties":false},"minItems":1,"maxItems":256},"fallback":{"$ref":"#/$defs/FormulaNode"}},"required":["operator","cases","fallback"],"additionalProperties":false}]},"ConditionNode":{"oneOf":[{"type":"object","properties":{"operator":{"const":"all"},"args":{"type":"array","items":{"$ref":"#/$defs/ConditionNode"},"minItems":1,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"any"},"args":{"type":"array","items":{"$ref":"#/$defs/ConditionNode"},"minItems":1,"maxItems":256}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"not"},"args":{"type":"array","items":{"$ref":"#/$defs/ConditionNode"},"minItems":1,"maxItems":1}},"required":["operator","args"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"eq"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"ne"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"lt"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"lte"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"gt"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"gte"},"left":{"$ref":"#/$defs/FormulaOperand"},"right":{"$ref":"#/$defs/FormulaOperand"}},"required":["operator","left","right"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"in"},"value":{"$ref":"#/$defs/FormulaOperand"},"values":{"type":"array","items":{"$ref":"#/$defs/FormulaOperand"},"minItems":1,"maxItems":256}},"required":["operator","value","values"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"exists"},"path":{"$ref":"#/$defs/StatePath"}},"required":["operator","path"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"before"},"at":{"$ref":"#/$defs/Timestamp"}},"required":["operator","at"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"after"},"at":{"$ref":"#/$defs/Timestamp"}},"required":["operator","at"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"elapsed_at_least"},"path":{"$ref":"#/$defs/StatePath"},"duration_seconds":{"type":"integer","minimum":0}},"required":["operator","path","duration_seconds"],"additionalProperties":false},{"type":"object","properties":{"operator":{"const":"predicate"},"name":{"$ref":"#/$defs/StableId"},"arguments":{"type":"object"}},"required":["operator","name","arguments"],"additionalProperties":false}]},"NetworkMode":{"enum":["offline","offline_first","online_optional","online_required","server_authoritative"]},"Dependency":{"type":"object","properties":{"module_id":{"$ref":"#/$defs/StableId"},"version_range":{"type":"string","minLength":1,"maxLength":128}},"required":["module_id","version_range"],"additionalProperties":false},"ReleaseLock":{"type":"object","properties":{"module_id":{"$ref":"#/$defs/StableId"},"version":{"type":"string","pattern":"^[0-9]+\\\\.[0-9]+\\\\.[0-9]+$"},"digest":{"type":"string","pattern":"^sha256:[a-f0-9]{64}$"}},"required":["module_id","version","digest"],"additionalProperties":false},"Blueprint":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"studio_id":{"$ref":"#/$defs/StableId"},"name":{"type":"string","minLength":1,"maxLength":128},"network_modes":{"type":"array","items":{"$ref":"#/$defs/NetworkMode"},"minItems":1,"uniqueItems":true},"features":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"allowed_modules":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"required_modules":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"resource_budget":{"$ref":"#/$defs/ResourceBudget"}},"required":["id","schema_version","studio_id","name","network_modes","features","allowed_modules","required_modules","resource_budget"],"additionalProperties":false},"ResourceBudget":{"type":"object","properties":{"max_formula_operations":{"type":"integer","minimum":1,"maximum":4096},"max_condition_nodes":{"type":"integer","minimum":1,"maximum":256},"max_ast_depth":{"type":"integer","minimum":1,"maximum":32},"max_events_per_action":{"type":"integer","minimum":0,"maximum":256}},"required":["max_formula_operations","max_condition_nodes","max_ast_depth","max_events_per_action"],"additionalProperties":false},"ExtensionRegistration":{"type":"object","properties":{"schema_id":{"type":"string","minLength":1,"maxLength":256},"digest":{"type":"string","pattern":"^sha256:[a-f0-9]{64}$"},"schema":{"type":"object","minProperties":1}},"required":["schema_id","digest","schema"],"additionalProperties":false},"ExtensionManifest":{"type":"object","properties":{"schema_version":{"$ref":"#/$defs/SchemaVersion"},"extensions":{"type":"object","propertyNames":{"pattern":"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$"},"additionalProperties":{"$ref":"#/$defs/ExtensionRegistration"},"maxProperties":64}},"required":["schema_version","extensions"],"additionalProperties":false},"PackageManifest":{"type":"object","properties":{"schema_version":{"$ref":"#/$defs/SchemaVersion"},"game":{"type":"string","pattern":"^(?!/)(?!.*(?:^|/)\\\\.\\\\.(?:/|$))[A-Za-z0-9._/-]+$"},"blueprint":{"type":"string","pattern":"^(?!/)(?!.*(?:^|/)\\\\.\\\\.(?:/|$))[A-Za-z0-9._/-]+$"},"modules":{"type":"array","items":{"type":"string","pattern":"^(?!/)(?!.*(?:^|/)\\\\.\\\\.(?:/|$))[A-Za-z0-9._/-]+$"},"maxItems":128},"extension_manifest":{"type":"string","pattern":"^(?!/)(?!.*(?:^|/)\\\\.\\\\.(?:/|$))[A-Za-z0-9._/-]+$"},"documents":{"type":"array","items":{"type":"string","pattern":"^(?!/)(?!.*(?:^|/)\\\\.\\\\.(?:/|$))[A-Za-z0-9._/-]+$"},"maxItems":4096}},"required":["schema_version","game","blueprint","modules","extension_manifest","documents"],"additionalProperties":false},"Entity":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"entity_type":{"type":"string","minLength":1},"initial_state":{"type":"object"},"properties":{"type":"object"},"relationships":{"type":"array","items":{"type":"object"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","entity_type","initial_state","properties","relationships"],"additionalProperties":false},"Resource":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"resource_type":{"type":"string"},"numeric_model":{"$ref":"#/$defs/NumericModel"},"initial_amount":{"$ref":"#/$defs/NumericValue"},"minimum":{"$ref":"#/$defs/NumericValue"},"maximum":{"$ref":"#/$defs/NumericValue"},"overflow_policy":{"enum":["reject","clamp","route_to_resource"]},"route_to_resource_id":{"$ref":"#/$defs/StableId"},"negative_balance_approval":{"type":"object","properties":{"review_id":{"$ref":"#/$defs/StableId"},"reviewer_role":{"const":"security_owner"},"approved":{"const":true},"resource_digest":{"type":"string","pattern":"^sha256:[a-f0-9]{64}$"}},"required":["review_id","reviewer_role","approved","resource_digest"],"additionalProperties":false},"visibility":{"enum":["public","private","server_only"]},"transfer_policy":{"enum":["non_transferable","game_internal","cross_game_contract"]}},"required":["id","schema_version","tags","enabled","metadata","extensions","resource_type","numeric_model","initial_amount","minimum","maximum","overflow_policy","visibility","transfer_policy"],"additionalProperties":false},"Condition":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"expression":{"$ref":"#/$defs/ConditionNode"}},"required":["id","schema_version","tags","enabled","metadata","extensions","expression"],"additionalProperties":false},"Formula":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"expression":{"$ref":"#/$defs/FormulaNode"},"variables":{"type":"array","items":{"type":"string","minLength":1},"uniqueItems":true,"maxItems":256}},"required":["id","schema_version","tags","enabled","metadata","extensions","expression","variables"],"additionalProperties":false},"Action":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"input_schema":{"type":"object"},"authority":{"enum":["local","server","match_server"]},"idempotency":{"type":"string"},"cooldown":{},"conditions":{"type":"array","items":{"$ref":"#/$defs/Condition"}},"costs":{"type":"array","items":{"$ref":"#/$defs/Cost"}},"effects":{"type":"array","items":{"$ref":"#/$defs/Effect"}},"rewards":{"type":"array","items":{"$ref":"#/$defs/Reward"}},"emitted_events":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"analytics":{"type":"array","items":{"type":"string"}},"rate_limit_class":{"type":"string"}},"required":["id","schema_version","tags","enabled","metadata","extensions","input_schema","authority","idempotency","cooldown","conditions","costs","effects","rewards","emitted_events","analytics","rate_limit_class"],"additionalProperties":false},"Cost":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"owner":{"$ref":"#/$defs/StableId"},"target":{"$ref":"#/$defs/Reference"},"quantity":{"$ref":"#/$defs/Formula"},"insufficiency":{"enum":["reject","partial"]},"ledger_reason":{"type":"string"}},"required":["id","schema_version","tags","enabled","metadata","extensions","owner","target","quantity","insufficiency","ledger_reason"],"additionalProperties":false},"Effect":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"operation":{"enum":["set","increment","decrement","append_unique","remove","unlock","lock","grant_item","consume_item","equip","unequip","apply_modifier","remove_modifier","start_timer","cancel_timer","complete_objective","emit_event"]},"path":{"$ref":"#/$defs/StatePath"},"target":{"$ref":"#/$defs/Reference"},"value":{}},"required":["id","schema_version","tags","enabled","metadata","extensions","operation","path","target","value"],"additionalProperties":false},"Reward":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"entries":{"type":"array","items":{"type":"object"},"minItems":1,"maxItems":256}},"required":["id","schema_version","tags","enabled","metadata","extensions","entries"],"additionalProperties":false},"Event":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"type":{"type":"string"},"major_version":{"type":"integer","minimum":1},"payload_schema":{"type":"object"},"producer":{"$ref":"#/$defs/StableId"},"allowed_consumers":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"retention_class":{"type":"string"},"contains_pii":{"type":"boolean"},"analytics_mapping":{"type":"string"}},"required":["id","schema_version","tags","enabled","metadata","extensions","type","major_version","payload_schema","producer","allowed_consumers","retention_class","contains_pii","analytics_mapping"],"additionalProperties":false},"Timer":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"timer_type":{"enum":["one_shot","recurring","countdown","cooldown","scheduled"]},"authority":{"enum":["server","match_server","local"]},"duration_formula":{"$ref":"#/$defs/Formula"},"schedule":{"type":"string"},"stacking_policy":{"type":"string"},"pause_policy":{"type":"string"},"on_due_action":{"$ref":"#/$defs/StableId"},"max_catch_up":{"type":"integer","minimum":0,"maximum":1000},"offline_policy":{"type":"string"}},"required":["id","schema_version","tags","enabled","metadata","extensions","timer_type","authority","duration_formula","schedule","stacking_policy","pause_policy","on_due_action","max_catch_up","offline_policy"],"additionalProperties":false},"Relationship":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"relationship_type":{"$ref":"#/$defs/StableId"},"target_type":{"type":"string"},"target_id":{"$ref":"#/$defs/StableId"}},"required":["id","schema_version","tags","enabled","metadata","extensions","relationship_type","target_type","target_id"],"additionalProperties":false},"ProgressionNode":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"graph_id":{"$ref":"#/$defs/StableId"},"node_type":{"type":"string"},"requirements":{"type":"array","items":{"$ref":"#/$defs/Condition"}},"costs":{"type":"array","items":{"$ref":"#/$defs/Cost"}},"rewards":{"type":"array","items":{"$ref":"#/$defs/Reward"}},"effects":{"type":"array","items":{"$ref":"#/$defs/Effect"}},"dependencies":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"exclusive_group":{"$ref":"#/$defs/StableId"},"repeat_policy":{"type":"string"},"children":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"entry":{"type":"boolean"},"required":{"type":"boolean"}},"required":["id","schema_version","tags","enabled","metadata","extensions","graph_id","node_type","requirements","costs","rewards","effects","dependencies","exclusive_group","repeat_policy","children"],"additionalProperties":false},"Game":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"studio_id":{"$ref":"#/$defs/StableId"},"name":{"type":"string","minLength":1,"maxLength":128},"genre_labels":{"type":"array","items":{"$ref":"#/$defs/Tag"},"maxItems":32},"default_locale":{"type":"string"},"supported_locales":{"type":"array","items":{"type":"string"},"minItems":1,"uniqueItems":true},"blueprint":{"$ref":"#/$defs/StableId"},"network_mode":{"$ref":"#/$defs/NetworkMode"},"engine_range":{"type":"string"},"modules":{"type":"array","items":{"$ref":"#/$defs/ReleaseLock"}},"features":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"state_schema_version":{"type":"string"},"definition_schema_version":{"$ref":"#/$defs/SchemaVersion"}},"required":["id","studio_id","name","genre_labels","default_locale","supported_locales","blueprint","network_mode","engine_range","modules","features","state_schema_version","definition_schema_version"],"additionalProperties":false},"Module":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"version":{"type":"string","pattern":"^[0-9]+\\\\.[0-9]+\\\\.[0-9]+$"},"digest":{"type":"string","pattern":"^sha256:[a-f0-9]{64}$"},"engine_range":{"type":"string"},"requires":{"type":"array","items":{"$ref":"#/$defs/Dependency"}},"conflicts":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"configuration":{"type":"object"},"state_namespaces":{"type":"array","items":{"$ref":"#/$defs/StableId"},"uniqueItems":true},"registered_actions":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"subscribed_events":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"emitted_events":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"registered_conditions":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"registered_effects":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"registered_timers":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"migrations":{"type":"array","items":{"type":"object"}},"resource_budget":{"$ref":"#/$defs/ResourceBudget"}},"required":["id","version","digest","engine_range","requires","conflicts","configuration","state_namespaces","registered_actions","subscribed_events","emitted_events","registered_conditions","registered_effects","registered_timers","migrations","resource_budget"],"additionalProperties":false},"Item":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"item_type":{"type":"string"},"stack_limit":{"type":"integer","minimum":1},"properties":{"type":"object"}},"required":["id","schema_version","tags","enabled","metadata","extensions","item_type","stack_limit","properties"],"additionalProperties":false},"Inventory":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"owner_type":{"type":"string"},"slot_limit":{"type":"integer","minimum":0},"accepted_items":{"type":"array","items":{"$ref":"#/$defs/StableId"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","owner_type","slot_limit","accepted_items"],"additionalProperties":false},"Quest":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"objectives":{"type":"array","items":{"type":"object"},"minItems":1},"requirements":{"type":"array","items":{"$ref":"#/$defs/Condition"}},"rewards":{"type":"array","items":{"$ref":"#/$defs/Reward"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","objectives","requirements","rewards"],"additionalProperties":false},"Achievement":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"requirements":{"type":"array","items":{"$ref":"#/$defs/Condition"}},"rewards":{"type":"array","items":{"$ref":"#/$defs/Reward"}},"repeatable":{"type":"boolean"}},"required":["id","schema_version","tags","enabled","metadata","extensions","requirements","rewards","repeatable"],"additionalProperties":false},"Entitlement":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"grant_type":{"type":"string"},"scope":{"type":"string"},"revocable":{"type":"boolean"}},"required":["id","schema_version","tags","enabled","metadata","extensions","grant_type","scope","revocable"],"additionalProperties":false},"Localization":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"locale":{"type":"string"},"entries":{"type":"object","propertyNames":{"pattern":"^[a-z][a-z0-9_.-]{2,127}$"},"additionalProperties":{"type":"string","maxLength":4096}}},"required":["id","schema_version","tags","enabled","metadata","extensions","locale","entries"],"additionalProperties":false},"LiveOps":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"starts_at":{"$ref":"#/$defs/Timestamp"},"ends_at":{"$ref":"#/$defs/Timestamp"},"configuration":{"type":"object"},"actions":{"type":"array","items":{"$ref":"#/$defs/StableId"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","starts_at","ends_at","configuration","actions"],"additionalProperties":false},"Experiment":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"variants":{"type":"array","items":{"type":"object"},"minItems":2},"allocation":{"type":"integer","minimum":0,"maximum":10000},"metrics":{"type":"array","items":{"type":"string"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","variants","allocation","metrics"],"additionalProperties":false},"Analytics":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"event_id":{"$ref":"#/$defs/StableId"},"fields":{"type":"object"},"contains_pii":{"const":false}},"required":["id","schema_version","tags","enabled","metadata","extensions","event_id","fields","contains_pii"],"additionalProperties":false},"Save":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"version":{"type":"integer","minimum":1},"namespaces":{"type":"array","items":{"$ref":"#/$defs/StableId"}},"migrations":{"type":"array","items":{"type":"object"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","version","namespaces","migrations"],"additionalProperties":false},"Match":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"mode":{"type":"string"},"authority":{"enum":["server","match_server"]},"rules":{"type":"object"},"participants":{"type":"integer","minimum":1}},"required":["id","schema_version","tags","enabled","metadata","extensions","mode","authority","rules","participants"],"additionalProperties":false},"CrossGameContract":{"type":"object","properties":{"id":{"$ref":"#/$defs/StableId"},"schema_version":{"$ref":"#/$defs/SchemaVersion"},"display_name_key":{"$ref":"#/$defs/LocalizationKey"},"description_key":{"$ref":"#/$defs/LocalizationKey"},"tags":{"$ref":"#/$defs/Tags"},"enabled":{"type":"boolean"},"metadata":{"$ref":"#/$defs/Metadata"},"extensions":{"$ref":"#/$defs/Extensions"},"source_game":{"$ref":"#/$defs/StableId"},"target_game":{"$ref":"#/$defs/StableId"},"contract_version":{"type":"string"},"allowed_rewards":{"type":"array","items":{"$ref":"#/$defs/StableId"}}},"required":["id","schema_version","tags","enabled","metadata","extensions","source_game","target_game","contract_version","allowed_rewards"],"additionalProperties":false},"DefinitionBundle":{"type":"object","properties":{"schema_version":{"$ref":"#/$defs/SchemaVersion"},"blueprint":{"$ref":"#/$defs/Blueprint"},"game":{"$ref":"#/$defs/Game"},"modules":{"type":"array","items":{"$ref":"#/$defs/Module"},"maxItems":128},"extension_manifest":{"$ref":"#/$defs/ExtensionManifest"},"documents":{"type":"array","items":{"oneOf":[{"$ref":"#/$defs/Entity"},{"$ref":"#/$defs/Resource"},{"$ref":"#/$defs/Condition"},{"$ref":"#/$defs/Formula"},{"$ref":"#/$defs/Action"},{"$ref":"#/$defs/Cost"},{"$ref":"#/$defs/Effect"},{"$ref":"#/$defs/Reward"},{"$ref":"#/$defs/Event"},{"$ref":"#/$defs/Timer"},{"$ref":"#/$defs/Relationship"},{"$ref":"#/$defs/ProgressionNode"},{"$ref":"#/$defs/Item"},{"$ref":"#/$defs/Inventory"},{"$ref":"#/$defs/Quest"},{"$ref":"#/$defs/Achievement"},{"$ref":"#/$defs/Entitlement"},{"$ref":"#/$defs/Localization"},{"$ref":"#/$defs/LiveOps"},{"$ref":"#/$defs/Experiment"},{"$ref":"#/$defs/Analytics"},{"$ref":"#/$defs/Save"},{"$ref":"#/$defs/Match"},{"$ref":"#/$defs/CrossGameContract"}]},"maxItems":4096}},"required":["schema_version","blueprint","game","modules","extension_manifest","documents"],"additionalProperties":false}},"$ref":"#/$defs/DefinitionBundle"}',
) as object;

const DEFINITION_SCHEMA_ID_V0_1 =
  "https://schemas.lengeas.internal/definition/v0.1/bundle.schema.json";
const definitionAjv = new Ajv2020({
  allErrors: true,
  ownProperties: true,
  strict: true,
  validateFormats: true,
});
addFormats(definitionAjv);
definitionAjv.addSchema(DEFINITION_SCHEMA_V0_1);

/**
 * Validate a generated Draft 2020-12 definition schema.
 * Select it by its stable definition name.
 */
export function validateDefinitionSchema<Name extends DefinitionSchemaName>(
  name: Name,
  value: unknown,
): DefinitionValidationResult<DefinitionTypeMap[Name]> {
  const validator = definitionAjv.getSchema(
    `${DEFINITION_SCHEMA_ID_V0_1}#/$defs/${name}`,
  );
  if (!validator) {
    throw new Error(`Generated definition schema not found: ${name}`);
  }
  if (validator(value)) {
    return { valid: true, value: value as DefinitionTypeMap[Name], errors: [] };
  }
  const errors = (validator.errors ?? []).map((error) => ({
    pointer: error.instancePath,
    code: "schema_validation" as const,
    severity: "error" as const,
  }));
  errors.sort((left, right) => {
    if (left.pointer < right.pointer) return -1;
    if (left.pointer > right.pointer) return 1;
    return 0;
  });
  return { valid: false, errors };
}

/**
 * Validate Draft 2020-12 bundle structure; semantic checks remain in the Python CLI.
 */
export function validateDefinitionBundle(
  value: unknown,
): DefinitionValidationResult<DefinitionBundle> {
  return validateDefinitionSchema("DefinitionBundle", value);
}
