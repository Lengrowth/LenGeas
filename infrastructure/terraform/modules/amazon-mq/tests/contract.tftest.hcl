run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "amazon-mq must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "amazon-mq"
    error_message = "amazon-mq must expose its module identity."
  }
}

