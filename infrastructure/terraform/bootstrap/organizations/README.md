# AWS Organizations bootstrap

This is the controlled adoption boundary for the seven-account model:
management, security, log-archive, shared-services, nonproduction, staging,
and production. It is disabled by default because account creation and Control
Tower adoption are account-level actions. Existing matching accounts must be
inventoried and imported rather than duplicated.

The module records the fail-closed SCP control set and accepts reviewed SCP JSON
documents. Control Tower, IAM Identity Center, organization CloudTrail, Config,
GuardDuty, Security Hub, central logging, budgets, and cost alerts must be
enabled in the control-plane implementation before this task can be marked
`in_review`.

## Example

See `examples/complete`.
