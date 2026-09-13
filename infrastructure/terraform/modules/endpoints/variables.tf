variable "enabled" {
  description = "Create persistent endpoints resources only after the Phase 02 owner gate."
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

variable "vpc_id" {
  type    = string
  default = ""
}

variable "subnet_ids" {
  type    = set(string)
  default = []
}

variable "security_group_ids" {
  type    = set(string)
  default = []
}

variable "service_names" {
  type    = set(string)
  default = ["ecr.api", "ecr.dkr", "logs", "secretsmanager", "kms", "ssm", "sts"]
}
