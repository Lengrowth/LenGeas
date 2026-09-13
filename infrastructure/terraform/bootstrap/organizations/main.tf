terraform {
  required_version = "= 1.15.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.62.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_organizations_organization" "this" {
  count                         = var.enabled ? 1 : 0
  aws_service_access_principals = var.service_access_principals
  feature_set                   = "ALL"
}

resource "aws_organizations_account" "environment" {
  for_each = var.enabled ? var.accounts : {}
  name     = each.value.name
  email    = each.value.email
  parent_id = try(
    var.parent_ids[each.value.parent],
    null
  )
  role_name = "OrganizationAccountAccessRole"
  tags      = merge(var.tags, { Environment = each.key })
}

resource "aws_organizations_policy" "scp" {
  for_each = var.enabled ? var.scps : {}
  name     = each.key
  content  = each.value
  type     = "SERVICE_CONTROL_POLICY"
}

resource "aws_organizations_policy_attachment" "scp" {
  for_each  = var.enabled ? var.scp_targets : {}
  policy_id = aws_organizations_policy.scp[each.value.policy].id
  target_id = each.value.target_id
}

resource "terraform_data" "control_plane" {
  input = {
    controls    = ["cloudtrail", "config", "guardduty", "securityhub", "iam-identity-center", "budgets", "central-logging"]
    fail_closed = true
  }
}
