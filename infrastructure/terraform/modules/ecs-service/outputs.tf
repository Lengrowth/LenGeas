output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "task_definition_arn" {
  value = try(aws_ecs_task_definition.this[0].arn, null)
}
