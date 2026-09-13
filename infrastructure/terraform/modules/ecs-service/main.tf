terraform {
  required_version = "= 1.15.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.62.0"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "ecs-service"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_ecs_task_definition" "this" {
  count                    = var.enabled ? 1 : 0
  family                   = "lengeas-${var.environment}-${var.service_name}"
  requires_compatibilities = ["EC2"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.execution_role_arn
  container_definitions = jsonencode([{
    name                   = var.service_name
    image                  = var.image
    essential              = true
    user                   = "10001"
    readonlyRootFilesystem = true
    linuxParameters        = { initProcessEnabled = true }
    portMappings           = [{ containerPort = 8080, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-region        = var.region
        awslogs-group         = "/aws/lengeas/${var.environment}/application"
        awslogs-stream-prefix = var.service_name
      }
    }
  }])
  tags = var.tags
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Task contract: private subnet, public_ip=false, non-root uid 10001, read-only filesystem, SSM administration, and no SSH/bastion.
