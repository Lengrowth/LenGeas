import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import {
  definitionSchemaNames,
  validateDefinitionBundle,
  validateDefinitionSchema,
} from "../../../packages/sdk-typescript/src/definition-v0_1.ts";

for (const name of definitionSchemaNames) {
  const result = validateDefinitionSchema(name, {});
  assert.equal(typeof result.valid, "boolean");
  assert.ok(Array.isArray(result.errors));
}

const fixturePath = resolve(
  "tests/conformance/fixtures/definitions/valid/minimal-bundle/canonical.json",
);
const bundle: unknown = JSON.parse(await readFile(fixturePath, "utf8"));
const accepted = validateDefinitionBundle(bundle);
assert.equal(accepted.valid, true);

const invalidBundle = {
  ...(bundle as Record<string, unknown>),
  unexpected: true,
};
const rejected = validateDefinitionBundle(invalidBundle);
assert.deepEqual(rejected, {
  valid: false,
  errors: [{ pointer: "", code: "schema_validation", severity: "error" }],
});

const sourceBundle = bundle as Record<string, Record<string, unknown>>;
const nestedInvalidBundle = {
  ...sourceBundle,
  game: { ...sourceBundle.game, unexpected: true },
  blueprint: { ...sourceBundle.blueprint, unexpected: true },
};
const nestedRejected = validateDefinitionBundle(nestedInvalidBundle);
assert.deepEqual(nestedRejected, {
  valid: false,
  errors: [
    { pointer: "/blueprint", code: "schema_validation", severity: "error" },
    { pointer: "/game", code: "schema_validation", severity: "error" },
  ],
});

const itemPath = resolve(
  "tests/conformance/fixtures/definitions/valid/item-record/canonical.json",
);
const item: unknown = JSON.parse(await readFile(itemPath, "utf8"));
assert.equal(validateDefinitionSchema("Item", item).valid, true);
const invalidItem = { ...(item as Record<string, unknown>), unexpected: true };
assert.deepEqual(validateDefinitionSchema("Item", invalidItem), {
  valid: false,
  errors: [{ pointer: "", code: "schema_validation", severity: "error" }],
});

console.log("PASS TypeScript definition and bundle validator fixtures");
