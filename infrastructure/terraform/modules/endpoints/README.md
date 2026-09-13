# Endpoints

Private interface and gateway endpoints for AWS control-plane services.

This module is disabled by default. It is composed by every environment root
without copied resource blocks. Persistent resources must be adopted/imported
when they already exist and must not be created from a console-only procedure.
Secrets are referenced by ARN/name only; values are never variables or state.

## Required controls

- owner, environment, service, cost-center, and data-class tags;
- private-by-default networking and encryption at rest;
- least-privilege identities and actionable alarms;
- an evidence record under `docs/evidence/phase-02/tasks/` before enablement.

## Example

See `examples/complete`.

