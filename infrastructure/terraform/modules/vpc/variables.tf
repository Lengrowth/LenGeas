variable "enabled" {
  description = "Create persistent vpc resources only after the Phase 02 owner gate."
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

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "availability_zones" {
  description = "Exactly three AZs in the selected region."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
  validation {
    condition     = length(var.availability_zones) == 3
    error_message = "Phase 02 requires exactly three availability zones."
  }
}

variable "enable_nat_gateways" {
  type    = bool
  default = true
}

variable "kms_key_arn" {
  description = "KMS key used to encrypt VPC flow logs."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.kms_key_arn != ""
    error_message = "kms_key_arn is required when vpc is enabled."
  }
}

variable "data_ingress_ports" {
  description = "Approved private data-plane ports reachable from ECS."
  type        = set(string)
  default     = ["6379", "5671", "9098"]
}

variable "network_insights_enabled" {
  description = "Create an explicit Reachability Analyzer path and analysis after reviewed ENI IDs are supplied."
  type        = bool
  default     = false
}

variable "reachability_source_id" {
  type    = string
  default = ""
}

variable "reachability_destination_id" {
  type    = string
  default = ""
}

variable "reachability_destination_port" {
  type    = number
  default = 6379
}
