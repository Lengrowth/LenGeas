module "github_oidc" {
  source      = "../../"
  repository  = "Lengrowth/LenGeas"
  branch      = "main"
  environment = "staging"
  enabled     = false
}
