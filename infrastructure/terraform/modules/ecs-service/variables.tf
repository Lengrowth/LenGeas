variable "enabled" {
  description = "Create persistent ecs-service resources only after the Phase 02 owner gate."
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

variable "cluster_name" {
  type    = string
  default = ""
  validation {
    condition     = !var.enabled || var.cluster_name != ""
    error_message = "cluster_name is required when ecs-service is enabled."
  }
}

variable "service_name" {
  type    = string
  default = "platform-api"
}

variable "image" {
  description = "Immutable ECR image digest; no mutable tag is accepted."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || can(regex("@sha256:[0-9a-f]{64}$", var.image))
    error_message = "Enabled ECS tasks require an immutable image digest."
  }
}

variable "subnet_ids" {
  type    = set(string)
  default = []
  validation {
    condition     = !var.enabled || length(var.subnet_ids) >= 3
    error_message = "Enabled ECS services require at least three private subnet IDs."
  }
}

variable "security_group_ids" {
  type    = set(string)
  default = []
  validation {
    condition     = !var.enabled || length(var.security_group_ids) >= 1
    error_message = "Enabled ECS services require an ECS security group ID."
  }
}

variable "task_role_arn" {
  type    = string
  default = ""
  validation {
    condition     = !var.enabled || var.task_role_arn != ""
    error_message = "task_role_arn is required when ecs-service is enabled."
  }
}

variable "execution_role_arn" {
  type    = string
  default = ""
  validation {
    condition     = !var.enabled || var.execution_role_arn != ""
    error_message = "execution_role_arn is required when ecs-service is enabled."
  }
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "capacity_provider" {
  type    = string
  default = "general"
  validation {
    condition     = contains(["general", "simulation", "realtime", "critical-workers"], var.capacity_provider)
    error_message = "capacity_provider must name one of the approved ECS capacity-provider classes."
  }
}

variable "target_group_arn" {
  description = "Optional ALB target group ARN for the API service."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.target_group_arn != ""
    error_message = "target_group_arn is required when ecs-service is enabled."
  }
}

variable "service_discovery_namespace_id" {
  description = "Private Cloud Map namespace for the service registry."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.service_discovery_namespace_id != ""
    error_message = "service_discovery_namespace_id is required when ecs-service is enabled."
  }
}
