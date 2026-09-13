variable "enabled" {
  description = "Enable persistent resources only after the owner cost/access gate."
  type        = bool
  default     = false
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "vpc_cidr" {
  type    = string
  default = "10.43.0.0/16"
}

variable "cloudflare_account_id" {
  description = "Non-secret Cloudflare account ID; required only when edge resources are enabled."
  type        = string
  default     = ""
}

variable "cloudflare_zone_name" {
  type    = string
  default = "lengeas.com"
}

variable "origin_base_url" {
  description = "HTTPS origin URL used by the edge gateway."
  type        = string
  default     = ""
}

variable "capacity_provider_arns" {
  description = "Approved ECS-optimized ARM64 ASG ARNs keyed by capacity-provider class."
  type        = map(string)
  default     = {}
}

variable "task_image" {
  description = "Immutable ECR image digest for the platform service."
  type        = string
  default     = ""
}

variable "task_role_arn" {
  type    = string
  default = ""
}

variable "execution_role_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type = map(string)
  default = {
    Project     = "LenGeas"
    Phase       = "02"
    Environment = "staging"
    ManagedBy   = "Terraform"
    OwnerRole   = "infrastructure_owner"
    CostCenter  = "platform"
    DataClass   = "platform"
  }
}
