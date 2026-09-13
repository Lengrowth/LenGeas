variable "enabled" {
  description = "Create the state backend only after the owner-approved bootstrap gate."
  type        = bool
  default     = false
}

variable "environment" {
  description = "Bootstrap environment label."
  type        = string
  default     = "management"
}

variable "region" {
  description = "AWS region containing the state bucket and KMS key."
  type        = string
  default     = "eu-central-1"
}

variable "bucket_name" {
  description = "Globally unique state bucket name; supplied only from approved configuration."
  type        = string
  default     = "lengeas-terraform-state-unset"
  validation {
    condition     = length(var.bucket_name) >= 3 && !strcontains(var.bucket_name, "secret")
    error_message = "bucket_name must be a non-secret, globally unique S3 name."
  }
}

variable "kms_key_policy" {
  description = "Optional reviewed KMS policy; defaults to the account-root recovery policy."
  type        = string
  default     = null
  nullable    = true
}

variable "tags" {
  description = "Required ownership and cost allocation tags."
  type        = map(string)
  default = {
    Project    = "LenGeas"
    Phase      = "02"
    ManagedBy  = "Terraform"
    DataClass  = "platform-control"
    CostCenter = "platform"
    OwnerRole  = "infrastructure_owner"
  }
}
