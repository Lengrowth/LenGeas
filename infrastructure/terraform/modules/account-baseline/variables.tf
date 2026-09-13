variable "enabled" {
  description = "Create persistent account-baseline resources only after the Phase 02 owner gate."
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

variable "audit_bucket_name" {
  description = "Existing or separately bootstrapped central log-archive bucket name."
  type        = string
  default     = ""
}

variable "audit_kms_key_arn" {
  description = "KMS key ARN for CloudTrail log encryption."
  type        = string
  default     = null
  nullable    = true
}

variable "config_role_arn" {
  description = "Reviewed AWS Config service role ARN."
  type        = string
  default     = ""
}

variable "organization_trail" {
  description = "Set true only in the organization management account after adoption."
  type        = bool
  default     = false
}

variable "budget_limit_usd" {
  description = "Approved monthly budget ceiling in USD. Zero keeps the budget disabled."
  type        = number
  default     = 0
  validation {
    condition     = var.budget_limit_usd >= 0
    error_message = "budget_limit_usd cannot be negative."
  }
}

variable "budget_email_addresses" {
  description = "Non-secret owner notification addresses for budget alerts."
  type        = set(string)
  default     = []
}
