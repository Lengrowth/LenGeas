variable "enabled" {
  description = "Create OIDC resources only after trust review."
  type        = bool
  default     = false
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "repository" {
  description = "Exact GitHub owner/repository allowed to assume the roles."
  type        = string
  default     = "Lengrowth/LenGeas"
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.repository))
    error_message = "repository must be owner/name."
  }
}

variable "branch" {
  description = "Protected branch permitted for plan trust."
  type        = string
  default     = "main"
}

variable "environment" {
  description = "GitHub environment permitted for apply trust."
  type        = string
  default     = "staging"
}

variable "github_thumbprints" {
  description = "Reviewed GitHub OIDC certificate thumbprints."
  type        = list(string)
  default     = []
  sensitive   = false
}

variable "plan_actions" {
  description = "Allowlisted read/plan actions; no write actions."
  type        = list(string)
  default     = ["sts:GetCallerIdentity", "s3:GetObject", "s3:ListBucket"]
}

variable "apply_actions" {
  description = "Reviewed apply action list; replace with resource-scoped policies before enablement."
  type        = list(string)
  default     = ["sts:GetCallerIdentity"]
}

variable "tags" {
  type = map(string)
  default = {
    Project    = "LenGeas"
    Phase      = "02"
    ManagedBy  = "Terraform"
    OwnerRole  = "infrastructure_owner"
    CostCenter = "platform"
  }
}
