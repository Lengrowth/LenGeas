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
  default = "nonproduction"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
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

variable "tags" {
  type = map(string)
  default = {
    Project     = "LenGeas"
    Phase       = "02"
    Environment = "nonproduction"
    ManagedBy   = "Terraform"
    OwnerRole   = "infrastructure_owner"
    CostCenter  = "platform"
    DataClass   = "platform"
  }
}

