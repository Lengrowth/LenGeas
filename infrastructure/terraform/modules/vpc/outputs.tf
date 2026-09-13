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

output "security_group_ids" {
  value = {
    alb      = try(aws_security_group.alb[0].id, null)
    ecs      = try(aws_security_group.ecs[0].id, null)
    data     = try(aws_security_group.data[0].id, null)
    endpoint = try(aws_security_group.endpoint[0].id, null)
  }
}

output "private_zone_id" {
  value = try(aws_route53_zone.private[0].zone_id, null)
}
