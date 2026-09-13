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
    module      = "kms-secrets"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_kms_key" "environment" {
  count                   = var.enabled ? 1 : 0
  description             = "LenGeas ${var.environment} secrets and data"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "this" {
  for_each    = var.enabled ? var.secret_names : toset([])
  name        = "lengeas/${var.environment}/${each.value}"
  description = "Empty Phase 02 secret container; value is provisioned out of band."
  kms_key_id  = aws_kms_key.environment[0].arn
  tags        = var.tags
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Secrets contract: KMS encryption and empty containers only; secret values never enter Terraform state.
