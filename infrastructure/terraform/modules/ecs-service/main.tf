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

resource "aws_ecs_service" "this" {
  count                  = var.enabled ? 1 : 0
  name                   = "lengeas-${var.environment}-${var.service_name}"
  cluster                = var.cluster_name
  task_definition        = aws_ecs_task_definition.this[0].arn
  desired_count          = var.desired_count
  enable_execute_command = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  capacity_provider_strategy {
    capacity_provider = var.capacity_provider
    weight            = 1
    base              = 1
  }
  network_configuration {
    subnets          = tolist(var.subnet_ids)
    security_groups  = tolist(var.security_group_ids)
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.service_name
    container_port   = 8080
  }
  lifecycle {
    ignore_changes = [desired_count]
  }
  tags = var.tags
}

resource "aws_appautoscaling_target" "service" {
  count              = var.enabled ? 1 : 0
  max_capacity       = max(var.desired_count * 4, 2)
  min_capacity       = var.desired_count
  resource_id        = "service/${var.cluster_name}/${aws_ecs_service.this[0].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  count              = var.enabled ? 1 : 0
  name               = "lengeas-${var.environment}-${var.service_name}-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.service[0].resource_id
  scalable_dimension = aws_appautoscaling_target.service[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.service[0].service_namespace
  target_tracking_scaling_policy_configuration {
    target_value = 60
    predefined_metric_specification { predefined_metric_type = "ECSServiceAverageCPUUtilization" }
  }
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Task contract: private subnet, public_ip=false, non-root uid 10001, read-only filesystem, SSM administration, and no SSH/bastion.
