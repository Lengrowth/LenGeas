variable "enabled" {
  description = "Create persistent ecs-cluster resources only after the Phase 02 owner gate."
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

variable "capacity_provider_arns" {
  description = "Optional pre-created ECS-optimized AL2023 ARM64 ASG ARNs to adopt by capacity class. Missing classes are provisioned by this module."
  type        = map(string)
  default     = {}
  validation {
    condition = alltrue([
      for key in keys(var.capacity_provider_arns) : contains(
        ["general", "simulation", "realtime", "critical-workers"],
        key
      )
    ])
    error_message = "capacity_provider_arns keys must be general, simulation, realtime, or critical-workers."
  }
}

variable "private_subnet_ids" {
  description = "Private application subnet IDs used by the ECS-optimized ASGs."
  type        = set(string)
  default     = []
  validation {
    condition     = !var.enabled || length(var.private_subnet_ids) >= 3
    error_message = "Enabled ECS clusters require private subnets in three AZs."
  }
}

variable "vpc_id" {
  description = "VPC ID for the private Cloud Map namespace."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || var.vpc_id != ""
    error_message = "vpc_id is required when ecs-cluster is enabled."
  }
}

variable "ami_id" {
  description = "Approved ECS-optimized Amazon Linux 2023 ARM64 AMI ID."
  type        = string
  default     = ""
  validation {
    condition     = !var.enabled || can(regex("^ami-[0-9a-f]+$", var.ami_id))
    error_message = "Enabled ECS clusters require an approved ARM64 ECS-optimized AMI ID."
  }
}

variable "instance_types" {
  description = "Graviton instance type per capacity class."
  type        = map(string)
  default = {
    general          = "m7g.large"
    simulation       = "c7g.large"
    realtime         = "c7g.large"
    critical-workers = "m7g.large"
  }
  validation {
    condition = alltrue([
      for key in ["general", "simulation", "realtime", "critical-workers"] :
      can(regex("^[mc]7g\\.", lookup(var.instance_types, key, "")))
    ])
    error_message = "ECS capacity classes must use documented Graviton m7g/c7g families."
  }
}

variable "min_size" {
  type    = number
  default = 1
  validation {
    condition     = var.min_size >= 0
    error_message = "min_size must be non-negative."
  }
}

variable "max_size" {
  type    = number
  default = 4
  validation {
    condition     = var.max_size >= var.min_size
    error_message = "max_size must be greater than or equal to min_size."
  }
}

variable "desired_capacity" {
  type    = number
  default = 1
  validation {
    condition     = var.desired_capacity >= var.min_size && var.desired_capacity <= var.max_size
    error_message = "desired_capacity must be between min_size and max_size."
  }
}
