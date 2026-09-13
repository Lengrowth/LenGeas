# Terraform backend bootstrap

Creates the versioned, KMS-encrypted S3 state bucket required by ADR-0010.
Terraform's native S3 lockfile is configured in the consuming roots with
`use_lockfile = true`; DynamoDB locking is deliberately not used. The module is
disabled by default because creating a globally named bucket is an external
cost/control-plane action.

Recovery: suspend applies, identify the last known-good version ID, copy it to a
quarantined recovery key, validate with `terraform show`, and restore only after
the owner records the recovery decision. Never delete state versions.

## Example

See `examples/complete` for a disabled-by-default configuration.
