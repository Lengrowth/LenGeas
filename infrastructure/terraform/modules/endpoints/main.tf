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
    module      = "endpoints"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_vpc_endpoint" "interface" {
  for_each            = var.enabled ? var.service_names : toset([])
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = tolist(var.subnet_ids)
  security_group_ids  = tolist(var.security_group_ids)
  private_dns_enabled = true
  tags                = merge(var.tags, { Name = "lengeas-${var.environment}-${each.value}" })
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Endpoint contract: private AWS endpoints and Atlas PrivateLink; public Atlas access is denied.
