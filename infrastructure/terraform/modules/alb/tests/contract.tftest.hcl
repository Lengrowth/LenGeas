run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "alb must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "alb"
    error_message = "alb must expose its module identity."
  }
}

