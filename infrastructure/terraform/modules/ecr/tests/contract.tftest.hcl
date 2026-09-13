run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "ecr must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "ecr"
    error_message = "ecr must expose its module identity."
  }
}

