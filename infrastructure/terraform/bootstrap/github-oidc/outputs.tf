output "plan_role_arn" {
  value = try(aws_iam_role.plan[0].arn, null)
}

output "apply_role_arn" {
  value = try(aws_iam_role.apply[0].arn, null)
}

output "subject_claims" {
  value = ["repo:${var.repository}:ref:refs/heads/${var.branch}", "repo:${var.repository}:environment:${var.environment}"]
}
