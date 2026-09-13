run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "account-baseline must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "account-baseline"
    error_message = "account-baseline must expose its module identity."
  }
}

