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
    module      = "ecs-cluster"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

locals {
  capacity_classes = toset(["general", "simulation", "realtime", "critical-workers"])
  internal_classes = var.enabled ? setsubtract(local.capacity_classes, toset(keys(var.capacity_provider_arns))) : toset([])
  spot_classes     = toset(["general", "simulation"])
}

resource "aws_iam_role" "ecs_instance" {
  count = var.enabled ? 1 : 0
  name  = "lengeas-${var.environment}-ecs-instance"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
  tags = var.tags
}

resource "aws_iam_instance_profile" "ecs" {
  count = var.enabled ? 1 : 0
  name  = "lengeas-${var.environment}-ecs-instance"
  role  = aws_iam_role.ecs_instance[0].name
  tags  = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_instance_ssm" {
  count      = var.enabled ? 1 : 0
  role       = aws_iam_role.ecs_instance[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ecs_instance_ecr" {
  count      = var.enabled ? 1 : 0
  role       = aws_iam_role.ecs_instance[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy" "ecs_instance_control_plane" {
  count = var.enabled ? 1 : 0
  name  = "ecs-control-plane"
  role  = aws_iam_role.ecs_instance[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:DeregisterContainerInstance",
        "ecs:DiscoverPollEndpoint",
        "ecs:Poll",
        "ecs:RegisterContainerInstance",
        "ecs:StartTelemetrySession",
        "ecs:Submit*",
        "ecs:TagResource",
        "ecs:UpdateContainerInstancesState"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_ecs_cluster" "this" {
  count = var.enabled ? 1 : 0
  name  = "lengeas-${var.environment}"
  setting {
    name  = "containerInsights"
    value = "enhanced"
  }
  tags = var.tags
}

resource "aws_service_discovery_private_dns_namespace" "this" {
  count       = var.enabled ? 1 : 0
  name        = "internal.lengeas"
  description = "Private service discovery namespace for ${var.environment}."
  vpc         = var.vpc_id
  tags        = var.tags
}

resource "aws_launch_template" "this" {
  for_each      = local.internal_classes
  name_prefix   = "lengeas-${var.environment}-${each.key}-"
  image_id      = var.ami_id
  instance_type = var.instance_types[each.key]
  user_data = base64encode(<<-USERDATA
    #!/bin/bash
    echo ECS_CLUSTER=lengeas-${var.environment} >> /etc/ecs/ecs.config
    echo ECS_ENABLE_CONTAINER_METADATA=true >> /etc/ecs/ecs.config
  USERDATA
  )
  iam_instance_profile {
    name = aws_iam_instance_profile.ecs[0].name
  }
  monitoring {
    enabled = true
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      encrypted             = true
      volume_size           = 50
      volume_type           = "gp3"
      delete_on_termination = true
    }
  }
  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "lengeas-${var.environment}-${each.key}" })
  }
  tags = var.tags
}

resource "aws_autoscaling_group" "this" {
  for_each                  = local.internal_classes
  name                      = "lengeas-${var.environment}-${each.key}"
  min_size                  = var.min_size
  max_size                  = var.max_size
  desired_capacity          = var.desired_capacity
  vpc_zone_identifier       = tolist(var.private_subnet_ids)
  health_check_type         = "EC2"
  health_check_grace_period = 300
  capacity_rebalance        = true
  protect_from_scale_in     = true
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.this[each.key].id
        version            = "$Latest"
      }
    }
    instances_distribution {
      on_demand_base_capacity                  = contains(local.spot_classes, each.key) ? 0 : 1
      on_demand_percentage_above_base_capacity = contains(local.spot_classes, each.key) ? 50 : 100
      spot_allocation_strategy                 = "capacity-optimized"
    }
  }
  tag {
    key                 = "AmazonECSManaged"
    value               = "true"
    propagate_at_launch = true
  }
  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

locals {
  effective_capacity_provider_arns = merge(
    var.capacity_provider_arns,
    { for name, group in aws_autoscaling_group.this : name => group.arn }
  )
}

resource "aws_ecs_capacity_provider" "this" {
  for_each = var.enabled ? local.effective_capacity_provider_arns : {}
  name     = "lengeas-${var.environment}-${each.key}"
  auto_scaling_group_provider {
    auto_scaling_group_arn = each.value
    managed_draining       = "ENABLED"
    managed_scaling {
      status                    = "ENABLED"
      target_capacity           = 100
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 2
    }
  }
  tags = var.tags
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  count              = var.enabled ? 1 : 0
  cluster_name       = aws_ecs_cluster.this[0].name
  capacity_providers = [for provider in aws_ecs_capacity_provider.this : provider.name]
  default_capacity_provider_strategy {
    capacity_provider = "lengeas-${var.environment}-general"
    weight            = 1
    base              = 1
  }
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Compute contract: general, simulation, realtime, and critical-workers capacity providers on Graviton m7g/c7g with managed_draining enabled. General/simulation use a controlled Spot mix; realtime/critical-workers are On-Demand.
