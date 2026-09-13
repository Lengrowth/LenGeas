variable "enabled" {
  description = "Adopt or create organization resources only after inventory and owner approval."
  type        = bool
  default     = false
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "accounts" {
  description = "Account requests keyed by environment; email values are non-secret owner contacts."
  type = map(object({
    name   = string
    email  = string
    parent = string
  }))
  default = {}
}

variable "parent_ids" {
  type    = map(string)
  default = {}
}

variable "scps" {
  description = "Named SCP JSON documents."
  type        = map(string)
  default     = {}
}

variable "scp_targets" {
  type = map(object({
    policy    = string
    target_id = string
  }))
  default = {}
}

variable "service_access_principals" {
  type    = list(string)
  default = ["cloudtrail.amazonaws.com", "config.amazonaws.com", "guardduty.amazonaws.com", "securityhub.amazonaws.com", "sso.amazonaws.com"]
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
