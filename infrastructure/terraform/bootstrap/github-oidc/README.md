# GitHub OIDC bootstrap

Creates short-lived plan and apply roles only when explicitly enabled. Trust is
restricted by issuer audience, exact repository, protected branch, and named
GitHub environment. The default apply action is intentionally harmless until a
resource-scoped policy is reviewed and supplied.

Long-lived AWS access keys are forbidden. Validate the rendered trust policy and
`aws sts get-caller-identity` in the OIDC workflow as evidence.

## Example

See `examples/complete`.
