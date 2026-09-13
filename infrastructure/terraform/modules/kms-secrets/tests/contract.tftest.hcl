run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "kms-secrets must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "kms-secrets"
    error_message = "kms-secrets must expose its module identity."
  }
}

