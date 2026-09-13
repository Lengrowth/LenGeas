run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "vpc must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "vpc"
    error_message = "vpc must expose its module identity."
  }
}

