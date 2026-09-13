run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "msk must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "msk"
    error_message = "msk must expose its module identity."
  }
}

