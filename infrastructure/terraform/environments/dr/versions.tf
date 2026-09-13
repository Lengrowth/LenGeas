terraform {
  required_version = "= 1.15.8"
  backend "s3" {
    key          = "lengeas/dr/terraform.tfstate"
    use_lockfile = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.62.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 5.24.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "= 2.17.0"
    }
    supabase = {
      source  = "supabase/supabase"
      version = "= 1.10.1"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = var.tags }
}

# All third-party provider credentials are read from provider-supported
# environment variables. They are intentionally absent from variables/state.
provider "cloudflare" {}
provider "mongodbatlas" {}
provider "supabase" {}
