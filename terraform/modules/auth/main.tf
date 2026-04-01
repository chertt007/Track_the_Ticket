# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Auth Module
# Cognito User Pool + Google IdP + App Client + SSM parameters
# Google credentials are read from Secrets Manager (not passed as variables)
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── Read Google credentials from Secrets Manager ──────────────────────────────

data "aws_secretsmanager_secret" "google_oauth" {
  name = "tracktheticket/google-oauth"
}

data "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id = data.aws_secretsmanager_secret.google_oauth.id
}

locals {
  google_creds = jsondecode(data.aws_secretsmanager_secret_version.google_oauth.secret_string)
}

# ── Cognito User Pool ─────────────────────────────────────────────────────────

resource "aws_cognito_user_pool" "main" {
  name = "tracktheticket-${var.environment}"

  # Sign in with email
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Cognito Hosted UI Domain ──────────────────────────────────────────────────
# URL: https://tracktheticket-prod.auth.us-east-1.amazoncognito.com

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "tracktheticket-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}

# ── Google Identity Provider ──────────────────────────────────────────────────

resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id                     = local.google_creds.client_id
    client_secret                 = local.google_creds.client_secret
    authorize_scopes              = "email openid profile"
    attributes_url                = "https://people.googleapis.com/v1/people/me?personFields="
    attributes_url_add_attributes = "true"
    authorize_url                 = "https://accounts.google.com/o/oauth2/v2/auth"
    oidc_issuer                   = "https://accounts.google.com"
    token_request_method          = "POST"
    token_url                     = "https://www.googleapis.com/oauth2/v4/token"
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
    name     = "name"
    picture  = "picture"
  }
}

# ── App Client ────────────────────────────────────────────────────────────────
# No client secret — SPA uses PKCE flow (Authorization Code + PKCE)

resource "aws_cognito_user_pool_client" "main" {
  name         = "tracktheticket-web-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false # SPA — no server to keep a secret

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  supported_identity_providers = ["COGNITO", "Google"]

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # Token validity
  access_token_validity  = 1  # hour
  id_token_validity      = 1  # hour
  refresh_token_validity = 30 # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  depends_on = [aws_cognito_identity_provider.google]
}

# ── SSM Parameters — consumed by API Lambda ───────────────────────────────────

resource "aws_ssm_parameter" "user_pool_id" {
  name  = "/tracktheticket/${var.environment}/cognito/user_pool_id"
  type  = "String"
  value = aws_cognito_user_pool.main.id

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "client_id" {
  name  = "/tracktheticket/${var.environment}/cognito/client_id"
  type  = "String"
  value = aws_cognito_user_pool_client.main.id

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "cognito_domain" {
  name  = "/tracktheticket/${var.environment}/cognito/domain"
  type  = "String"
  value = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
