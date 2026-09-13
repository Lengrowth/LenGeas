run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "ecs-service must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "ecs-service"
    error_message = "ecs-service must expose its module identity."
  }
}

