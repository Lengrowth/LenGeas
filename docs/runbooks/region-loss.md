# Region loss

The candidate production regions are `eu-central-1` primary and `eu-west-1` DR. A rollout ADR must confirm or supersede them before use. Run a regional recovery only after production activation, with owner/incident-commander authorization and synthetic exercise data.

Provision the DR root from Terraform, restore Atlas to the approved point-in-time, recover R2/catalog exports, validate secrets by name, bring up ECS/ALB/Valkey/RabbitMQ/MSK, run integrity/smoke checks, then change Cloudflare origin routing. The target is RTO four hours and persistent-data RPO fifteen minutes. Do not route traffic before restore and integrity checks pass.
