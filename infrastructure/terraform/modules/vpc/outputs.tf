output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "vpc_id" {
  value = try(aws_vpc.this[0].id, null)
}

output "public_subnet_ids" {
  value = [for subnet in aws_subnet.public_alb : subnet.id]
}

output "private_subnet_ids" {
  value = [for subnet in aws_subnet.private_app : subnet.id]
}

output "isolated_subnet_ids" {
  value = [for subnet in aws_subnet.isolated : subnet.id]
}
