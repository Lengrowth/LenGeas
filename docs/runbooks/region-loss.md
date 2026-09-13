# Region loss

The primary region is `eu-central-1`; DR is `eu-west-1`. Run a regional recovery only with owner/incident-commander authorization and synthetic data.

Provision the DR root from Terraform, restore Atlas to the approved point-in-time, recover R2/catalog exports, validate secrets by name, bring up ECS/ALB/Valkey/RabbitMQ/MSK, run integrity/smoke checks, then change Cloudflare origin routing. The target is RTO four hours and persistent-data RPO fifteen minutes. Do not route traffic before restore and integrity checks pass.
