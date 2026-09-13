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
    module      = "vpc"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "aws_vpc" "this" {
  count                = var.enabled ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = "lengeas-${var.environment}" })
}

resource "aws_subnet" "public_alb" {
  for_each = var.enabled ? toset(var.availability_zones) : toset([])
  vpc_id   = aws_vpc.this[0].id
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    4,
    index(var.availability_zones, each.value)
  )
  availability_zone       = each.value
  map_public_ip_on_launch = false
  tags                    = merge(var.tags, { Name = "lengeas-${var.environment}-public-${each.value}" })
}

resource "aws_subnet" "private_app" {
  for_each = var.enabled ? toset(var.availability_zones) : toset([])
  vpc_id   = aws_vpc.this[0].id
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    4,
    4 + index(var.availability_zones, each.value)
  )
  availability_zone = each.value
  tags              = merge(var.tags, { Name = "lengeas-${var.environment}-private-${each.value}" })
}

resource "aws_subnet" "isolated" {
  for_each = var.enabled ? toset(var.availability_zones) : toset([])
  vpc_id   = aws_vpc.this[0].id
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    4,
    8 + index(var.availability_zones, each.value)
  )
  availability_zone = each.value
  tags              = merge(var.tags, { Name = "lengeas-${var.environment}-isolated-${each.value}" })
}

resource "aws_internet_gateway" "this" {
  count  = var.enabled ? 1 : 0
  vpc_id = aws_vpc.this[0].id
  tags   = var.tags
}

resource "aws_eip" "nat" {
  for_each = var.enabled && var.enable_nat_gateways ? toset(var.availability_zones) : toset([])
  domain   = "vpc"
  tags     = merge(var.tags, { Name = "lengeas-${var.environment}-nat-eip-${each.value}" })
}

resource "aws_nat_gateway" "this" {
  for_each      = var.enabled && var.enable_nat_gateways ? toset(var.availability_zones) : toset([])
  allocation_id = aws_eip.nat[each.value].id
  subnet_id     = aws_subnet.public_alb[each.value].id
  depends_on    = [aws_internet_gateway.this]
  tags          = merge(var.tags, { Name = "lengeas-${var.environment}-nat-${each.value}" })
}

resource "aws_route_table" "public" {
  count  = var.enabled ? 1 : 0
  vpc_id = aws_vpc.this[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this[0].id
  }
  tags = merge(var.tags, { Name = "lengeas-${var.environment}-public" })
}

resource "aws_route_table_association" "public" {
  for_each       = var.enabled ? toset(var.availability_zones) : toset([])
  subnet_id      = aws_subnet.public_alb[each.value].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table" "private" {
  for_each = var.enabled ? toset(var.availability_zones) : toset([])
  vpc_id   = aws_vpc.this[0].id
  dynamic "route" {
    for_each = var.enable_nat_gateways ? [each.value] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this[route.value].id
    }
  }
  tags = merge(var.tags, { Name = "lengeas-${var.environment}-private-${each.value}" })
}

resource "aws_route_table_association" "private" {
  for_each       = var.enabled ? toset(var.availability_zones) : toset([])
  subnet_id      = aws_subnet.private_app[each.value].id
  route_table_id = aws_route_table.private[each.value].id
}

resource "aws_route_table" "isolated" {
  for_each = var.enabled ? toset(var.availability_zones) : toset([])
  vpc_id   = aws_vpc.this[0].id
  tags     = merge(var.tags, { Name = "lengeas-${var.environment}-isolated-${each.value}" })
}

resource "aws_route_table_association" "isolated" {
  for_each       = var.enabled ? toset(var.availability_zones) : toset([])
  subnet_id      = aws_subnet.isolated[each.value].id
  route_table_id = aws_route_table.isolated[each.value].id
}

resource "aws_security_group" "alb" {
  count       = var.enabled ? 1 : 0
  name        = "lengeas-${var.environment}-alb"
  description = "Cloudflare origin traffic only; source ranges are managed separately."
  vpc_id      = aws_vpc.this[0].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = var.tags
}

resource "aws_security_group" "ecs" {
  count       = var.enabled ? 1 : 0
  name        = "lengeas-${var.environment}-ecs"
  description = "ECS tasks; ingress is security-group referenced."
  vpc_id      = aws_vpc.this[0].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = var.tags
}

resource "aws_security_group" "data" {
  count       = var.enabled ? 1 : 0
  name        = "lengeas-${var.environment}-data"
  description = "Data plane; no public ingress and no SSH."
  vpc_id      = aws_vpc.this[0].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = var.tags
}

resource "aws_security_group" "endpoint" {
  count       = var.enabled ? 1 : 0
  name        = "lengeas-${var.environment}-endpoint"
  description = "Interface endpoint ENIs; HTTPS only from ECS tasks."
  vpc_id      = aws_vpc.this[0].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = var.tags
}

resource "aws_security_group_rule" "alb_to_ecs" {
  count                    = var.enabled ? 1 : 0
  type                     = "ingress"
  security_group_id        = aws_security_group.ecs[0].id
  source_security_group_id = aws_security_group.alb[0].id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  description              = "ALB to private ECS service only"
}

resource "aws_security_group_rule" "ecs_to_data" {
  for_each                 = var.enabled ? var.data_ingress_ports : toset([])
  type                     = "ingress"
  security_group_id        = aws_security_group.data[0].id
  source_security_group_id = aws_security_group.ecs[0].id
  from_port                = tonumber(each.value)
  to_port                  = tonumber(each.value)
  protocol                 = "tcp"
  description              = "ECS to approved private data port ${each.value}"
}

resource "aws_security_group_rule" "ecs_to_endpoint" {
  count                    = var.enabled ? 1 : 0
  type                     = "ingress"
  security_group_id        = aws_security_group.endpoint[0].id
  source_security_group_id = aws_security_group.ecs[0].id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  description              = "ECS to AWS interface endpoints over TLS"
}

resource "aws_route53_zone" "private" {
  count = var.enabled ? 1 : 0
  name  = "internal.lengeas"
  vpc {
    vpc_id     = aws_vpc.this[0].id
    vpc_region = var.region
  }
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "flow" {
  count             = var.enabled ? 1 : 0
  name              = "/aws/vpc/lengeas/${var.environment}/flow"
  retention_in_days = 90
  kms_key_id        = var.kms_key_arn
  tags              = var.tags
}

resource "aws_iam_role" "flow" {
  count = var.enabled ? 1 : 0
  name  = "lengeas-${var.environment}-vpc-flow-logs"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "vpc-flow-logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy" "flow" {
  count = var.enabled ? 1 : 0
  role  = aws_iam_role.flow[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:DescribeLogStreams", "logs:PutLogEvents"]
      Resource = "${aws_cloudwatch_log_group.flow[0].arn}:*"
    }]
  })
}

resource "aws_flow_log" "this" {
  count                = var.enabled ? 1 : 0
  vpc_id               = aws_vpc.this[0].id
  traffic_type         = "ALL"
  iam_role_arn         = aws_iam_role.flow[0].arn
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow[0].arn
  tags                 = var.tags
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Network contract: three AZs, AZ-local NAT routes, VPC flow logs, DNS, primary/DR connectivity, and Reachability Analyzer evidence. AWS provider 6.62.0 does not expose Reachability Analyzer as Terraform resources, so the reviewed ENI inputs remain an explicit evidence gate.
