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

resource "aws_iam_openid_connect_provider" "github" {
  count           = var.enabled ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = var.github_thumbprints
  tags            = var.tags
}

data "aws_iam_policy_document" "trust" {
  statement {
    sid     = "GitHubActionsRestrictedTrust"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [try(aws_iam_openid_connect_provider.github[0].arn, "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com")]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.repository}:ref:refs/heads/${var.branch}", "repo:${var.repository}:environment:${var.environment}"]
    }
  }
}

resource "aws_iam_role" "plan" {
  count              = var.enabled ? 1 : 0
  name               = "lengeas-${var.environment}-github-plan"
  assume_role_policy = data.aws_iam_policy_document.trust.json
  tags               = var.tags
}

resource "aws_iam_role" "apply" {
  count              = var.enabled ? 1 : 0
  name               = "lengeas-${var.environment}-github-apply"
  assume_role_policy = data.aws_iam_policy_document.trust.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "plan" {
  count = var.enabled ? 1 : 0
  role  = aws_iam_role.plan[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "StateReadAndPlanOnly"
      Effect   = "Allow"
      Action   = var.plan_actions
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "apply" {
  count = var.enabled ? 1 : 0
  role  = aws_iam_role.apply[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "ApprovedApplyActions"
      Effect   = "Allow"
      Action   = var.apply_actions
      Resource = "*"
    }]
  })
}
