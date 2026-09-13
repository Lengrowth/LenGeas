module "iam" {
  source      = "../../"
  environment = "example"
  region      = "eu-central-1"
  enabled     = false
  controls    = ["encryption", "private", "owner-tags", "alarm"]
}

