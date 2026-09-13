variable "enabled" {
  description = "Create persistent msk resources only after the Phase 02 owner gate."
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

variable "subnet_ids" {
  type    = set(string)
  default = []
  validation {
    condition     = !var.enabled || length(var.subnet_ids) >= 3
    error_message = "Enabled MSK Serverless requires isolated subnets in three AZs."
  }
}

variable "security_group_ids" {
  type    = set(string)
  default = []
  validation {
    condition     = !var.enabled || length(var.security_group_ids) >= 1
    error_message = "Enabled MSK Serverless requires a data security group."
  }
}
