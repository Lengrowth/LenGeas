run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "atlas must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "atlas"
    error_message = "atlas must expose its module identity."
  }
}

