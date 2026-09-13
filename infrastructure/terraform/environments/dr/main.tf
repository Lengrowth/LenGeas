locals {
  controls = toset([
    "encryption", "private-network", "owner-tags", "audit", "backup", "alarms",
    "no-public-ip", "no-root-container", "no-ssh", "origin-authentication"
  ])
}

module "account_baseline" {
  source      = "../../modules/account-baseline"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "vpc" {
  source      = "../../modules/vpc"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
  vpc_cidr    = var.vpc_cidr
}
module "endpoints" {
  source             = "../../modules/endpoints"
  enabled            = var.enabled
  environment        = var.environment
  region             = var.region
  controls           = local.controls
  tags               = var.tags
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = toset(module.vpc.isolated_subnet_ids)
  security_group_ids = toset(compact([module.vpc.security_group_ids["ecs"]]))
}
module "ecr" {
  source      = "../../modules/ecr"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "ecs_cluster" {
  source                 = "../../modules/ecs-cluster"
  enabled                = var.enabled
  environment            = var.environment
  region                 = var.region
  controls               = local.controls
  tags                   = var.tags
  capacity_provider_arns = var.capacity_provider_arns
}
module "ecs_service" {
  source             = "../../modules/ecs-service"
  enabled            = var.enabled
  environment        = var.environment
  region             = var.region
  controls           = local.controls
  tags               = var.tags
  cluster_name       = module.ecs_cluster.cluster_name
  capacity_provider  = try(module.ecs_cluster.capacity_provider_names["general"], "")
  image              = var.task_image
  task_role_arn      = coalesce(module.iam.ecs_task_role_arn, var.task_role_arn)
  execution_role_arn = coalesce(module.iam.ecs_execution_role_arn, var.execution_role_arn)
  subnet_ids         = toset(module.vpc.private_subnet_ids)
  security_group_ids = toset(compact([module.vpc.security_group_ids["ecs"]]))
  target_group_arn   = module.alb.target_group_arn
}
module "alb" {
  source             = "../../modules/alb"
  enabled            = var.enabled
  environment        = var.environment
  region             = var.region
  controls           = local.controls
  tags               = var.tags
  subnet_ids         = toset(module.vpc.public_subnet_ids)
  security_group_ids = toset(compact([module.vpc.security_group_ids["alb"]]))
  vpc_id             = module.vpc.vpc_id
}
module "iam" {
  source      = "../../modules/iam"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "kms_secrets" {
  source      = "../../modules/kms-secrets"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "atlas" {
  source      = "../../modules/atlas"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "valkey" {
  source             = "../../modules/valkey"
  enabled            = var.enabled
  environment        = var.environment
  region             = var.region
  controls           = local.controls
  tags               = var.tags
  subnet_ids         = toset(module.vpc.isolated_subnet_ids)
  security_group_ids = toset(compact([module.vpc.security_group_ids["data"]]))
}
module "amazon_mq" {
  source      = "../../modules/amazon-mq"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "msk" {
  source             = "../../modules/msk"
  enabled            = var.enabled
  environment        = var.environment
  region             = var.region
  controls           = local.controls
  tags               = var.tags
  subnet_ids         = toset(module.vpc.isolated_subnet_ids)
  security_group_ids = toset(compact([module.vpc.security_group_ids["data"]]))
}
module "observability" {
  source      = "../../modules/observability"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
  kms_key_arn = module.kms_secrets.kms_key_arn
}
module "cloudflare_zone" {
  source          = "../../modules/cloudflare-zone"
  enabled         = var.enabled
  environment     = var.environment
  region          = var.region
  controls        = local.controls
  tags            = var.tags
  account_id      = var.cloudflare_account_id
  origin_hostname = coalesce(module.alb.dns_name, "origin.internal.invalid")
  zone_name       = var.cloudflare_zone_name
}
module "cloudflare_worker" {
  source          = "../../modules/cloudflare-worker"
  enabled         = var.enabled
  environment     = var.environment
  region          = var.region
  controls        = local.controls
  tags            = var.tags
  account_id      = var.cloudflare_account_id
  zone_id         = module.cloudflare_zone.zone_id
  zone_name       = var.cloudflare_zone_name
  origin_base_url = var.origin_base_url
}
module "r2" {
  source      = "../../modules/r2"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
  account_id  = var.cloudflare_account_id
}
module "supabase" {
  source      = "../../modules/supabase"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
module "resend" {
  source      = "../../modules/resend"
  enabled     = var.enabled
  environment = var.environment
  region      = var.region
  controls    = local.controls
  tags        = var.tags
}
