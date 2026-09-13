output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "audit_trail_arn" {
  value = try(aws_cloudtrail.organization[0].arn, null)
}

output "guardduty_detector_id" {
  value = try(aws_guardduty_detector.this[0].id, null)
}
