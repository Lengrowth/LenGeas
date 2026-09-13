run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "valkey must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "valkey"
    error_message = "valkey must expose its module identity."
  }
}

