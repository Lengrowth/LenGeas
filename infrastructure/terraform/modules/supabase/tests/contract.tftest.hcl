run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "supabase must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "supabase"
    error_message = "supabase must expose its module identity."
  }
}

