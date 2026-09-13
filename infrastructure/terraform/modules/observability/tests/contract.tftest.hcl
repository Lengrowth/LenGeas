run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "observability must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "observability"
    error_message = "observability must expose its module identity."
  }
}

