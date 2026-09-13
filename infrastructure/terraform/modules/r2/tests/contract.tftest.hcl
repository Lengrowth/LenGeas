run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "r2 must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "r2"
    error_message = "r2 must expose its module identity."
  }
}

