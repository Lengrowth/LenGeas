output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "cluster_arn" {
  value = try(aws_msk_serverless_cluster.this[0].arn, null)
}
