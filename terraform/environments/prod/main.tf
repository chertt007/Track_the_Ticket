terraform {
  required_version = ">= 1.6"

  # Remote state in S3 — create this bucket manually once before first apply:
  # aws s3 mb s3://tracktheticket-terraform-state --region us-east-1
  backend "s3" {
    bucket = "tracktheticket-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "frontend" {
  source = "../../modules/frontend"

  bucket_name = var.frontend_bucket_name
  environment = "prod"
}
