variable "enabled" {
  description = "Create persistent observability resources only after the Phase 02 owner gate."
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

variable "log_retention_days" {
  type    = number
  default = 90
}

variable "kms_key_arn" {
  description = "KMS key for CloudWatch log encryption."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.kms_key_arn != ""
    error_message = "kms_key_arn is required when observability is enabled."
  }
}
