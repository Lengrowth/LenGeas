terraform {
  required_version = "= 1.15.8"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 5.24.0"
    }
  }
}

resource "terraform_data" "contract" {
  input = {
    module      = "cloudflare-zone"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "cloudflare_zone" "this" {
  count = var.enabled ? 1 : 0
  account = {
    id = var.account_id
  }
  name = var.zone_name
  type = "full"
}

resource "cloudflare_dns_record" "api" {
  count   = var.enabled ? 1 : 0
  zone_id = cloudflare_zone.this[0].id
  name    = "api"
  type    = "CNAME"
  content = var.origin_hostname
  proxied = true
  ttl     = 1
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Edge contract: proxied DNS, TLS, managed WAF, DDoS, bot/Turnstile/Access capability checks, rate rules, origin-authentication, and direct-origin denial.
