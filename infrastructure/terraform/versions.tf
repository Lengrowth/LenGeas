terraform {
  required_version = "= 1.15.8"

  backend "s3" {
    # Bucket, key, region, and KMS settings are supplied by a reviewed environment bootstrap.
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
