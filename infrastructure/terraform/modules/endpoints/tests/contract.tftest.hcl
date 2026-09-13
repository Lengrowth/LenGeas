run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "endpoints must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "endpoints"
    error_message = "endpoints must expose its module identity."
  }
}

