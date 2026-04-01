terraform {
  required_version = ">= 1.6"

  # Remote state in S3 — create this bucket manually once before first apply:
  # aws s3 mb s3://tracktheticket-terraform-state --region us-east-1
  # aws dynamodb create-table \
  #   --table-name tracktheticket-terraform-locks \
  #   --attribute-definitions AttributeName=LockID,AttributeType=S \
  #   --key-schema AttributeName=LockID,KeyType=HASH \
  #   --billing-mode PAY_PER_REQUEST \
  #   --region us-east-1
  backend "s3" {
    bucket         = "tracktheticket-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tracktheticket-terraform-locks"
    encrypt        = true
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

  default_tags {
    tags = {
      Project     = "TrackTheTicket"
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

# ── Frontend: S3 (frontend + screenshots) + CloudFront ────────────────────────

module "frontend" {
  source = "../../modules/frontend"

  bucket_name             = var.frontend_bucket_name
  screenshots_bucket_name = var.screenshots_bucket_name
  environment             = "prod"
}

# ── Networking: VPC + private subnets + security groups ──────────────────────
# Uncomment when TF-05 is implemented

# module "networking" {
#   source      = "../../modules/networking"
#   environment = "prod"
# }

# ── Auth: Cognito + Google OAuth 2.0 ─────────────────────────────────────────
# Uncomment when TF-AUTH-01 is implemented

# module "auth" {
#   source               = "../../modules/auth"
#   environment          = "prod"
#   google_client_id     = var.google_client_id
#   google_client_secret = var.google_client_secret
#   callback_urls        = [module.frontend.cloudfront_url]
# }

# ── Database: PostgreSQL RDS ──────────────────────────────────────────────────
# Uncomment when TF-DB-01 is implemented

# module "database" {
#   source                = "../../modules/database"
#   environment           = "prod"
#   db_name               = var.db_name
#   db_username           = var.db_username
#   db_password           = var.db_password
#   private_subnet_ids    = module.networking.private_subnet_ids
#   rds_security_group_id = module.networking.rds_security_group_id
# }

# ── API: Lambda Docker + API Gateway HTTP v2 ──────────────────────────────────
# Uncomment when TF-API-01 is implemented

# module "api" {
#   source                   = "../../modules/api"
#   environment              = "prod"
#   ecr_image_uri            = var.ecr_image_uri
#   vpc_id                   = module.networking.vpc_id
#   private_subnet_ids       = module.networking.private_subnet_ids
#   lambda_security_group_id = module.networking.lambda_security_group_id
#   db_endpoint              = module.database.db_endpoint
#   db_name                  = module.database.db_name
#   db_username              = var.db_username
#   db_password              = var.db_password
#   cognito_user_pool_id     = module.auth.user_pool_id
#   cognito_client_id        = module.auth.user_pool_client_id
#   screenshots_bucket_arn   = module.frontend.screenshots_bucket_arn
# }

# ── Messaging: SQS + EventBridge cron (3x/day) ───────────────────────────────
# Uncomment when TF-MESSAGING-01 is implemented

# module "messaging" {
#   source                   = "../../modules/messaging"
#   environment              = "prod"
#   price_checker_lambda_arn = module.api.lambda_function_arn
# }
