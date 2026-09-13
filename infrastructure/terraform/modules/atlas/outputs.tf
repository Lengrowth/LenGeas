output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "project_id" {
  value = try(mongodbatlas_project.this[0].id, null)
}

output "cluster_id" {
  value = try(mongodbatlas_advanced_cluster.this[0].cluster_id, null)
}
