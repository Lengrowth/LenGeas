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
    module      = "alb"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_lb" "this" {
  count                      = var.enabled ? 1 : 0
  name                       = "lengeas-${var.environment}"
  internal                   = var.internal
  load_balancer_type         = "application"
  subnets                    = tolist(var.subnet_ids)
  security_groups            = tolist(var.security_group_ids)
  enable_deletion_protection = var.environment == "production"
  drop_invalid_header_fields = true
  tags                       = var.tags
}

resource "aws_lb_target_group" "api" {
  count       = var.enabled ? 1 : 0
  name        = "lengeas-${var.environment}-api"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id
  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }
  tags = var.tags
}

resource "aws_lb_listener" "https" {
  count             = var.enabled && var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.this[0].arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = var.certificate_arn
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api[0].arn
  }
}

resource "aws_security_group_rule" "cloudflare_https" {
  count             = var.enabled && length(var.cloudflare_source_ranges) > 0 && length(var.security_group_ids) > 0 ? 1 : 0
  type              = "ingress"
  security_group_id = tolist(var.security_group_ids)[0]
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = tolist(var.cloudflare_source_ranges)
  description       = "Cloudflare origin traffic only"
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Origin contract: Cloudflare source ranges plus authenticated origin traffic; direct-origin access is denied.
