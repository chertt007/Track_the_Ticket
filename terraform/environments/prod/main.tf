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

# ── Networking: VPC + public/private subnets + security groups ───────────────

module "networking" {
  source      = "../../modules/networking"
  environment = "prod"
  aws_region  = "us-east-1"
}

# ── Auth: Cognito + Google OAuth 2.0 ─────────────────────────────────────────

module "auth" {
  source      = "../../modules/auth"
  environment = "prod"
  aws_region  = "us-east-1"

  callback_urls = [
    "${module.frontend.cloudfront_url}/dashboard",
    "http://localhost:5173/dashboard",
  ]

  logout_urls = [
    "${module.frontend.cloudfront_url}/login",
    "http://localhost:5173/login",
  ]
}

# ── Database: PostgreSQL RDS ──────────────────────────────────────────────────

module "database" {
  source      = "../../modules/database"
  environment = "prod"

  db_name     = "tracktheticket"
  db_username = var.db_username
  db_password = var.db_password

  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.public_subnet_ids  # Public subnets for dev public access
  rds_security_group_id = module.networking.rds_security_group_id
}

# ── Price-Checker: browser-use Lambda + SQS + EventBridge cron ───────────────

module "price_checker" {
  source      = "../../modules/price-checker"
  environment = "prod"

  db_endpoint = module.database.db_endpoint
  db_name     = module.database.db_name
  db_username = var.db_username
  db_password = var.db_password

  screenshots_bucket_name = module.frontend.screenshots_bucket_name
  screenshots_bucket_arn  = module.frontend.screenshots_bucket_arn

  openrouter_api_key = var.openrouter_api_key

  langfuse_public_key = var.langfuse_public_key
  langfuse_secret_key = var.langfuse_secret_key
}

# ── API: Lambda Docker + API Gateway HTTP v2 ──────────────────────────────────

module "api" {
  source      = "../../modules/api"
  environment = "prod"
  aws_region  = "us-east-1"

  db_endpoint = module.database.db_endpoint
  db_name     = module.database.db_name
  db_username = var.db_username
  db_password = var.db_password

  cognito_user_pool_id = module.auth.user_pool_id
  cognito_client_id    = module.auth.client_id

  screenshots_bucket_name = module.frontend.screenshots_bucket_name
  screenshots_bucket_arn  = module.frontend.screenshots_bucket_arn

  # Wire up SQS so POST /check dispatches to price-checker Lambda instead of running inline
  price_checker_queue_url = module.price_checker.queue_url
  price_checker_queue_arn = module.price_checker.queue_arn
}
