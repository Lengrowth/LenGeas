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

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Network contract: three AZs, AZ-local NAT routes, VPC flow logs, DNS, primary/DR connectivity, and Reachability Analyzer evidence.
