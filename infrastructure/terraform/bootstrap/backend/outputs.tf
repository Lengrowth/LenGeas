output "bucket_name" {
  description = "State bucket name."
  value       = try(aws_s3_bucket.state[0].bucket, null)
}

output "kms_key_arn" {
  description = "KMS key ARN for state encryption."
  value       = try(aws_kms_key.state[0].arn, null)
}

output "lockfile_mode" {
  description = "Required backend locking mode."
  value       = "use_lockfile = true"
}
