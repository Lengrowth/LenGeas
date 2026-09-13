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
    module      = "cloudflare-worker"
    environment = var.environment
    enabled     = var.enabled
    ownership   = var.tags.OwnerRole
    cost_center = var.tags.CostCenter
    controls    = var.controls
  }
}

resource "cloudflare_worker" "this" {
  count      = var.enabled ? 1 : 0
  account_id = var.account_id
  name       = "${var.worker_name}-${var.environment}"
  logpush    = true
  observability = {
    enabled            = true
    head_sampling_rate = 1
    logs = {
      enabled            = true
      invocation_logs    = true
      persist            = true
      head_sampling_rate = 1
    }
  }
  tags = ["project:lengeas", "environment:${var.environment}"]
}

resource "cloudflare_worker_version" "this" {
  count       = var.enabled ? 1 : 0
  account_id  = var.account_id
  worker_id   = cloudflare_worker.this[0].name
  main_module = "index.js"
  modules = [{
    name         = "index.js"
    content_file = "${path.module}/edge-gateway.js"
    content_type = "application/javascript+module"
  }]
  bindings = [{
    name = "ORIGIN_BASE_URL"
    text = var.origin_base_url
    type = "plain_text"
  }]
  annotations = {
    workers_message = "LenGeas Phase 02 edge gateway skeleton"
    workers_tag     = var.environment
  }
}

resource "cloudflare_workers_deployment" "this" {
  count       = var.enabled ? 1 : 0
  account_id  = var.account_id
  script_name = cloudflare_worker.this[0].name
  strategy    = "percentage"
  versions = [{
    percentage = 100
    version_id = cloudflare_worker_version.this[0].id
  }]
}

resource "cloudflare_workers_route" "api" {
  count   = var.enabled ? 1 : 0
  zone_id = var.zone_id
  pattern = "api.${var.zone_name}/*"
  script  = cloudflare_worker.this[0].name
}

# Provider resources are intentionally gated by var.enabled. The environment
# roots remain plan-safe until account inventory, vendor access, and cost gates
# are recorded in docs/evidence/phase-02.
# Worker contract: environment separation, R2 bindings, logs, W3C trace context, request limits, and authenticated origin headers.
