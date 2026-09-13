output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "endpoints" {
  value = { for name, group in aws_elasticache_replication_group.this : name => group.primary_endpoint_address }
}
