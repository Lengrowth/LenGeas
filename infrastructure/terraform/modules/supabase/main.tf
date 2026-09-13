terraform {
  required_version = "= 1.15.8"
  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "= 1.10.1"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "supabase"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Identity contract: environment-separated projects, asymmetric signing keys, documented JWKS, and no password in Terraform state.
