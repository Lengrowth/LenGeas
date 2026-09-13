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

resource "mongodbatlas_project" "this" {
  count            = var.enabled ? 1 : 0
  name             = "LenGeas-${var.environment}"
  org_id           = var.organization_id
  project_owner_id = var.project_owner_id != "" ? var.project_owner_id : null
}

resource "mongodbatlas_advanced_cluster" "this" {
  count          = var.enabled ? 1 : 0
  project_id     = mongodbatlas_project.this[0].id
  name           = "lengeas-${var.environment}-documents"
  cluster_type   = "REPLICASET"
  backup_enabled = true
  pit_enabled    = true
  replication_specs = [{
    id = "lengeas-${var.environment}-primary"
    region_configs = [{
      region_name   = var.atlas_region
      provider_name = "AWS"
      priority      = 7
      electable_specs = {
        instance_size = var.cluster_instance_size
        node_count    = 3
      }
    }]
  }]
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Atlas contract: dedicated three-node, backups, point-in-time restore, AWS PrivateLink, and public-access denial. PrivateLink endpoint attachment remains a separate capability-gated integration because its AWS endpoint service ID is returned only after Atlas access is authorized.
# Atlas public access is denied; ECS connectivity uses AWS PrivateLink only.
