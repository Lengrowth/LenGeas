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
    module      = "account-baseline"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_cloudtrail" "organization" {
  count                         = var.enabled && var.audit_bucket_name != "" ? 1 : 0
  name                          = "lengeas-${var.environment}-organization"
  s3_bucket_name                = var.audit_bucket_name
  include_global_service_events = true
  is_multi_region_trail         = true
  is_organization_trail         = var.organization_trail
  enable_log_file_validation    = true
  enable_logging                = true
  kms_key_id                    = var.audit_kms_key_arn
  tags                          = var.tags
}

resource "aws_config_delivery_channel" "this" {
  count          = var.enabled && var.audit_bucket_name != "" && var.config_role_arn != "" ? 1 : 0
  name           = "lengeas-${var.environment}"
  s3_bucket_name = var.audit_bucket_name
  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }
}

resource "aws_config_configuration_recorder" "this" {
  count    = var.enabled && var.config_role_arn != "" ? 1 : 0
  name     = "lengeas-${var.environment}"
  role_arn = var.config_role_arn
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_configuration_recorder_status" "this" {
  count      = length(aws_config_configuration_recorder.this) > 0 && length(aws_config_delivery_channel.this) > 0 ? 1 : 0
  name       = aws_config_configuration_recorder.this[0].name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

resource "aws_guardduty_detector" "this" {
  count                        = var.enabled ? 1 : 0
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  tags                         = var.tags
}

resource "aws_securityhub_account" "this" {
  count                    = var.enabled ? 1 : 0
  enable_default_standards = true
  auto_enable_controls     = true
}

resource "aws_budgets_budget" "monthly" {
  count        = var.enabled && var.budget_limit_usd > 0 && length(var.budget_email_addresses) > 0 ? 1 : 0
  name         = "lengeas-${var.environment}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  cost_filter {
    name   = "TagKeyValue"
    values = ["Project$LenGeas"]
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = tolist(var.budget_email_addresses)
  }
  tags = var.tags
}

# Organization controls remain fail-closed until adoption is proven: root-use,
# cross-account escalation, disabled-audit, and prohibited-region/action SCPs.

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Control contract: Control Tower, organization CloudTrail, AWS Config, GuardDuty, Security Hub, budgets, SCPs, root-use deny, cross-account escalation deny, and central logging.
