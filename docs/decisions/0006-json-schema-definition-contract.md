# ADR-0006 — JSON Schema definition contract

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Definition owner; Schema owner
- Supersedes: none
- Superseded by: none

## Context

Definitions are authored as YAML, validated and transported as canonical JSON, versioned independently, and consumed by Studio, runtime, SDKs, and AI tools. The contract must reject executable content and preserve deterministic digests.

## Decision

Use JSON Schema Draft 2020-12 as the canonical definition contract. YAML is the authoring format; canonical JSON is used for validation, hashing, storage, and transport. Published definitions contain immutable resolved module versions and digests.

## Consequences

The shared schema supports generated types and the same public API for humans and AI. It requires compatibility rules, schema generation, reference checks, and validation evidence.

## Rejected designs

- Arbitrary code-based definitions: rejected because executable content is prohibited.
- Unversioned ad hoc JSON: rejected because published contracts require schema versions and digest-addressed bundles.

## Validation

Schema valid/invalid fixtures, reference and graph checks, compatibility tests, canonical hashing, and generated type checks are required before production rollout.

## Rollout and reversal

Introduce additive compatible schema changes first, publish exact schema digests, and migrate definitions through staged validation. Breaking semantics require a new major schema and migration plan.
