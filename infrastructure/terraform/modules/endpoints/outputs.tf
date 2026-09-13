output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "endpoint_ids" {
  value = { for name, endpoint in aws_vpc_endpoint.interface : name => endpoint.id }
}
