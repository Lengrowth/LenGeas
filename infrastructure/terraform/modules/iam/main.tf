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
    module      = "iam"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

data "aws_iam_policy_document" "ecs_tasks_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  count              = var.enabled ? 1 : 0
  name               = "lengeas-${var.environment}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_trust.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  count      = var.enabled ? 1 : 0
  role       = aws_iam_role.ecs_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  count              = var.enabled ? 1 : 0
  name               = "lengeas-${var.environment}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_trust.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "ecs_task_deny_escalation" {
  count = var.enabled ? 1 : 0
  name  = "deny-escalation"
  role  = aws_iam_role.ecs_task[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "DenyPrivilegeEscalation"
      Effect   = "Deny"
      Action   = ["iam:*", "organizations:*", "sts:AssumeRole"]
      Resource = "*"
    }]
  })
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# IAM contract: least-privilege task roles, SSM-only administration, and cross-account escalation denied.
