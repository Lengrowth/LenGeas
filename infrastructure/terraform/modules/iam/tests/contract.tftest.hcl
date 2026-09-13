run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "iam must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "iam"
    error_message = "iam must expose its module identity."
  }
}

