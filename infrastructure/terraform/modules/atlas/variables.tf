variable "enabled" {
  description = "Create persistent atlas resources only after the Phase 02 owner gate."
  type        = bool
  default     = false
}

variable "environment" {
  description = "Logical environment name."
  type        = string
}

variable "region" {
  description = "Primary region for this module."
  type        = string
  default     = "eu-central-1"
}

variable "controls" {
  description = "Reviewed control assertions attached to the module contract."
  type        = set(string)
  default     = []
}

variable "tags" {
  description = "Required ownership and cost allocation tags."
  type        = map(string)
  default = {
    Project    = "LenGeas"
    Phase      = "02"
    ManagedBy  = "Terraform"
    OwnerRole  = "infrastructure_owner"
    CostCenter = "platform"
    DataClass  = "platform"
  }
}

variable "organization_id" {
  description = "MongoDB Atlas organization ID; non-secret."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.organization_id != ""
    error_message = "organization_id is required when Atlas is enabled."
  }
}

variable "project_owner_id" {
  description = "Optional Atlas project owner user ID; non-secret."
  type        = string
  default     = ""
}

variable "cluster_instance_size" {
  description = "Atlas dedicated instance size."
  type        = string
  default     = "M10"
}

variable "atlas_region" {
  description = "Atlas AWS region code for the primary replica set."
  type        = string
  default     = "EU_CENTRAL_1"
}
