// Generated from packages/schemas/definition/v0.1/bundle.schema.json. Do not edit.

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
