run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "resend must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "resend"
    error_message = "resend must expose its module identity."
  }
}

