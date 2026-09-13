output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "ecs_execution_role_arn" {
  value = try(aws_iam_role.ecs_execution[0].arn, null)
}

output "ecs_task_role_arn" {
  value = try(aws_iam_role.ecs_task[0].arn, null)
}
