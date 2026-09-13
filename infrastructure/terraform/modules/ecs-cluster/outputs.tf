output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "cluster_name" {
  value = try(aws_ecs_cluster.this[0].name, null)
}

output "capacity_provider_names" {
  value = { for name, provider in aws_ecs_capacity_provider.this : name => provider.name }
}

output "general_capacity_provider_name" {
  value = try(aws_ecs_capacity_provider.this["general"].name, null)
}

output "capacity_asg_arns" {
  value = { for name, group in aws_autoscaling_group.this : name => group.arn }
}

output "instance_profile_name" {
  value = try(aws_iam_instance_profile.ecs[0].name, null)
}

output "service_discovery_namespace_id" {
  value = try(aws_service_discovery_private_dns_namespace.this[0].id, null)
}
