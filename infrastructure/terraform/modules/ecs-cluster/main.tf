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
    module      = "ecs-cluster"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_ecs_cluster" "this" {
  count = var.enabled ? 1 : 0
  name  = "lengeas-${var.environment}"
  setting {
    name  = "containerInsights"
    value = "enhanced"
  }
  tags = var.tags
}

resource "aws_ecs_capacity_provider" "this" {
  for_each = var.enabled ? var.capacity_provider_arns : {}
  name     = "lengeas-${var.environment}-${each.key}"
  auto_scaling_group_provider {
    auto_scaling_group_arn = each.value
    managed_draining       = "ENABLED"
    managed_scaling {
      status                    = "ENABLED"
      target_capacity           = 100
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 2
    }
  }
  tags = var.tags
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  count              = var.enabled && length(var.capacity_provider_arns) > 0 ? 1 : 0
  cluster_name       = aws_ecs_cluster.this[0].name
  capacity_providers = [for provider in aws_ecs_capacity_provider.this : provider.name]
  default_capacity_provider_strategy {
    capacity_provider = "lengeas-${var.environment}-general"
    weight            = 1
    base              = 1
  }
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Compute contract: general, simulation, realtime, and critical-workers capacity providers on Graviton m7g/c7g with managed_draining enabled.
