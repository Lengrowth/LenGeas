terraform {
  required_version = "= 1.15.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.62.0"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "observability"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_cloudwatch_log_group" "application" {
  count             = var.enabled ? 1 : 0
  name              = "/aws/lengeas/${var.environment}/application"
  retention_in_days = var.log_retention_days
  kms_key_id        = null
  tags              = var.tags
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Observability contract: OpenTelemetry, CloudWatch, AMP, AMG, X-Ray, Sentry, alert routing, and cost alarms.
