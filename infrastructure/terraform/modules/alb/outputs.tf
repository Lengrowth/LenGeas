output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "dns_name" {
  value = try(aws_lb.this[0].dns_name, null)
}

output "arn" {
  value = try(aws_lb.this[0].arn, null)
}
