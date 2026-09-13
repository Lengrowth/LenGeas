run "disabled_contract" {
  command = plan

  variables {
    environment = "example"
    enabled     = false
  }

  assert {
    condition     = output.enabled == false
    error_message = "cloudflare-zone must be disabled in its safe example."
  }

  assert {
    condition     = output.contract.module == "cloudflare-zone"
    error_message = "cloudflare-zone must expose its module identity."
  }
}

