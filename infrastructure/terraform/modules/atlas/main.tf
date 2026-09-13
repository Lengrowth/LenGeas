terraform {
  required_version = "= 1.15.8"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "= 2.17.0"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "atlas"
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
# Atlas contract: dedicated three-node, backups, point-in-time restore, AWS PrivateLink, and public-access denial.
# Atlas public access is denied; ECS connectivity uses AWS PrivateLink only.
