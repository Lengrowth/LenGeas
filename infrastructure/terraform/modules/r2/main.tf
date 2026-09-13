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
  for_each      = var.enabled ? var.bucket_names : toset([])
  account_id    = var.account_id
  name          = "lengeas-${var.environment}-${each.value}"
  location      = "eeur"
  storage_class = "Standard"
}

locals {
  retention_days = {
    definitions       = 3650
    assets-quarantine = 30
    assets-approved   = 3650
    simulation        = 365
    analytics         = 730
    audit             = 3650
  }
}

resource "cloudflare_r2_bucket_lifecycle" "this" {
  for_each    = var.enabled ? var.bucket_names : toset([])
  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.this[each.value].name
  rules = [{
    id      = "expire-objects"
    enabled = true
    conditions = {
      prefix = ""
    }
    delete_objects_transition = {
      condition = {
        type    = "Age"
        max_age = local.retention_days[each.value] * 86400
      }
    }
    abort_multipart_uploads_transition = {
      condition = {
        type    = "Age"
        max_age = 7 * 86400
      }
    }
  }]
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# R2 contract: private environment/data-class buckets, lifecycle, and scoped bindings.
# Cloudflare R2 exposes lifecycle but not bucket-versioning as a Terraform resource in
# provider 5.24.0; versioning remains an explicit provider-capability gate.
