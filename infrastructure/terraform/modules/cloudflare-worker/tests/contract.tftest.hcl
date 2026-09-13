run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "cloudflare-worker must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "cloudflare-worker"
    error_message = "cloudflare-worker must expose its module identity."
  }
}

