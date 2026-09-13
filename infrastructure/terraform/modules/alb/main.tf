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
    module      = "alb"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_lb" "this" {
  count                      = var.enabled ? 1 : 0
  name                       = "lengeas-${var.environment}"
  internal                   = var.internal
  load_balancer_type         = "application"
  subnets                    = tolist(var.subnet_ids)
  security_groups            = tolist(var.security_group_ids)
  enable_deletion_protection = var.environment == "production"
  drop_invalid_header_fields = true
  tags                       = var.tags
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Origin contract: Cloudflare source ranges plus authenticated origin traffic; direct-origin access is denied.
