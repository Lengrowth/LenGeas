terraform {
  required_version = "= 1.15.8"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 5.24.0"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "r2"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "cloudflare_r2_bucket" "this" {
  for_each   = var.enabled ? var.bucket_names : toset([])
  account_id = var.account_id
  name       = "lengeas-${var.environment}-${each.value}"
  location   = "eeur"
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# R2 contract: private environment/data-class buckets, versioning, lifecycle, and scoped bindings.
