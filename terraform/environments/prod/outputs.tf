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
