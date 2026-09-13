variable "enabled" {
  description = "Create persistent alb resources only after the Phase 02 owner gate."
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
    error_message = "Enabled ALBs require at least three public subnet IDs."
  }
}

variable "security_group_ids" {
  type    = set(string)
  default = []
  validation {
    condition     = !var.enabled || length(var.security_group_ids) >= 1
    error_message = "Enabled ALBs require an ALB security group ID."
  }
}

variable "internal" {
  description = "ALB is public only as a Cloudflare-allowlisted edge origin."
  type        = bool
  default     = false
}

variable "vpc_id" {
  type    = string
  default = ""
  validation {
    condition     = !var.enabled || var.vpc_id != ""
    error_message = "vpc_id is required when alb is enabled."
  }
}

variable "certificate_arn" {
  description = "Origin TLS certificate ARN; HTTPS listener is not created without it."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.certificate_arn != ""
    error_message = "certificate_arn is required when alb is enabled."
  }
}

variable "cloudflare_source_ranges" {
  description = "Current Cloudflare published source ranges, supplied from reviewed inventory."
  type        = set(string)
  default     = []
  validation {
    condition     = !var.enabled || length(var.cloudflare_source_ranges) > 0
    error_message = "Enabled ALBs require reviewed Cloudflare source ranges."
  }
}
