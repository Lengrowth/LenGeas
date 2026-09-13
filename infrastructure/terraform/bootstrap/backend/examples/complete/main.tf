module "backend" {
  source      = "../../"
  environment = "management"
  region      = "eu-central-1"
  bucket_name = "lengeas-terraform-state-example"
  enabled     = false
}
