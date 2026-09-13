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
    module      = "valkey"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_elasticache_subnet_group" "this" {
  for_each   = var.enabled ? var.boundary_names : toset([])
  name       = "lengeas-${var.environment}-${each.value}"
  subnet_ids = tolist(var.subnet_ids)
  tags       = merge(var.tags, { DataBoundary = each.value })
}

resource "aws_elasticache_replication_group" "this" {
  for_each                   = var.enabled ? var.boundary_names : toset([])
  replication_group_id       = "lengeas-${var.environment}-${each.value}"
  description                = "LenGeas ${var.environment} Valkey ${each.value} boundary"
  engine                     = "valkey"
  engine_version             = "8.0"
  node_type                  = "cache.t4g.small"
  num_cache_clusters         = 3
  multi_az_enabled           = true
  automatic_failover_enabled = true
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.this[each.value].name
  security_group_ids         = tolist(var.security_group_ids)
  snapshot_retention_limit   = 7
  snapshot_window            = "03:00-04:00"
  maintenance_window         = "sun:04:00-sun:05:00"
  apply_immediately          = false
  auto_minor_version_upgrade = true
  tags                       = merge(var.tags, { DataBoundary = each.value })
  lifecycle {
    prevent_destroy = true
  }
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Valkey contract: version 8, TLS, ACLs, Multi-AZ, automatic failover, cache/realtime separation.
# Authentication remains an explicit ACL/IAM capability gate; no password is read into Terraform state.
