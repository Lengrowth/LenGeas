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

resource "cloudflare_zone_setting" "security" {
  for_each = var.enabled ? {
    always_use_https = "on"
    min_tls_version  = "1.2"
    tls_1_3          = "on"
  } : {}
  zone_id    = cloudflare_zone.this[0].id
  setting_id = each.key
  value      = each.value
}

resource "cloudflare_ruleset" "api_rate_limit" {
  count       = var.enabled ? 1 : 0
  zone_id     = cloudflare_zone.this[0].id
  name        = "lengeas-${var.environment}-api-rate-limit"
  description = "Protect the API edge from abusive request bursts."
  kind        = "zone"
  phase       = "http_ratelimit"
  rules = [{
    action      = "block"
    description = "API request rate limit"
    enabled     = true
    expression  = "(http.host eq \"api.${var.zone_name}\")"
    ratelimit = {
      characteristics     = ["ip.src"]
      period              = 10
      requests_per_period = 100
    }
  }]
}

resource "cloudflare_ruleset" "unsafe_methods" {
  count       = var.enabled ? 1 : 0
  zone_id     = cloudflare_zone.this[0].id
  name        = "lengeas-${var.environment}-unsafe-methods"
  description = "Block methods that the public API does not expose."
  kind        = "zone"
  phase       = "http_request_firewall_custom"
  rules = [{
    action      = "block"
    description = "Disallowed HTTP method"
    enabled     = true
    expression  = "(http.request.method in {\"TRACE\" \"CONNECT\"})"
  }]
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Edge contract: proxied DNS, TLS, managed WAF, DDoS, bot/Turnstile/Access capability checks, rate rules, origin-authentication, and direct-origin denial.
