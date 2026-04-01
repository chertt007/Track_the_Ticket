# ── Frontend outputs ──────────────────────────────────────────────────────────

output "frontend_url" {
  description = "Live frontend URL"
  value       = module.frontend.cloudfront_url
}

output "s3_bucket" {
  description = "Frontend S3 bucket name — add as S3_BUCKET in GitHub Secrets"
  value       = module.frontend.bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID — add as CLOUDFRONT_DISTRIBUTION_ID in GitHub Secrets"
  value       = module.frontend.cloudfront_distribution_id
}

output "screenshots_bucket" {
  description = "Screenshots S3 bucket name — add as SCREENSHOTS_BUCKET in GitHub Secrets"
  value       = module.frontend.screenshots_bucket_name
}

# ── Auth outputs ─────────────────────────────────────────────────────────────

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID — add as VITE_COGNITO_USER_POOL_ID in GitHub Secrets"
  value       = module.auth.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito App Client ID — add as VITE_COGNITO_CLIENT_ID in GitHub Secrets"
  value       = module.auth.client_id
}

output "cognito_domain" {
  description = "Cognito Hosted UI domain — add as VITE_COGNITO_DOMAIN in GitHub Secrets"
  value       = module.auth.cognito_domain
}

output "google_redirect_uri" {
  description = "Add this URI to Google OAuth App → Authorized redirect URIs"
  value       = module.auth.google_redirect_uri
}

# ── Networking outputs ────────────────────────────────────────────────────────

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs — used by RDS and Lambda"
  value       = module.networking.private_subnet_ids
}

# ── Database outputs ──────────────────────────────────────────────────────────

output "db_endpoint" {
  description = "RDS endpoint — copy to DB Access page in Notion"
  value       = module.database.db_endpoint
}

output "db_secrets_manager_arn" {
  description = "Secrets Manager ARN — add to Lambda IAM policy"
  value       = module.database.secrets_manager_arn
}

# ── Outputs added as modules are implemented ──────────────────────────────────

# output "api_endpoint" {
#   description = "API Gateway endpoint — add as VITE_API_URL in frontend build"
#   value       = module.api.api_endpoint
# }

# output "cognito_user_pool_id" {
#   description = "Cognito User Pool ID — add as VITE_COGNITO_USER_POOL_ID"
#   value       = module.auth.user_pool_id
# }

# output "cognito_client_id" {
#   description = "Cognito App Client ID — add as VITE_COGNITO_CLIENT_ID"
#   value       = module.auth.user_pool_client_id
# }
