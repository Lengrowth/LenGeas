run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "ecs-cluster must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "ecs-cluster"
    error_message = "ecs-cluster must expose its module identity."
  }
}

