output "contract" {
  description = "Machine-readable module contract and control assertions."
  value       = terraform_data.contract.output
}

output "enabled" {
  description = "Whether this module was enabled for the plan/apply."
  value       = var.enabled
}

output "bucket_names" {
  value = { for name, bucket in cloudflare_r2_bucket.this : name => bucket.name }
}
