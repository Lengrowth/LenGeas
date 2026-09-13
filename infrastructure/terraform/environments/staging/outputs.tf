output "environment" {
  value = var.environment
}

output "region" {
  value = var.region
}

output "module_contracts" {
  value = {
    account_baseline  = module.account_baseline.contract
    vpc               = module.vpc.contract
    endpoints         = module.endpoints.contract
    ecr               = module.ecr.contract
    ecs_cluster       = module.ecs_cluster.contract
    ecs_service       = module.ecs_service.contract
    alb               = module.alb.contract
    iam               = module.iam.contract
    kms_secrets       = module.kms_secrets.contract
    atlas             = module.atlas.contract
    valkey            = module.valkey.contract
    amazon_mq         = module.amazon_mq.contract
    msk               = module.msk.contract
    observability     = module.observability.contract
    cloudflare_zone   = module.cloudflare_zone.contract
    cloudflare_worker = module.cloudflare_worker.contract
    r2                = module.r2.contract
    supabase          = module.supabase.contract
    resend            = module.resend.contract
  }
}

