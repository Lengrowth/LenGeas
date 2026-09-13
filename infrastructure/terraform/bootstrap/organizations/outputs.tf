output "organization_id" {
  value = try(aws_organizations_organization.this[0].id, null)
}

output "account_ids" {
  value = { for name, account in aws_organizations_account.environment : name => account.id }
}

output "required_controls" {
  value = ["root-use-deny", "cross-account-escalation-deny", "audit-disable-deny", "prohibited-region-deny", "prohibited-action-deny"]
}
