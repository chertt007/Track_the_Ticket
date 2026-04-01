output "user_pool_id" {
  description = "Cognito User Pool ID — set as VITE_COGNITO_USER_POOL_ID in GitHub Secrets"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN — used in API Gateway JWT authorizer"
  value       = aws_cognito_user_pool.main.arn
}

output "client_id" {
  description = "Cognito App Client ID — set as VITE_COGNITO_CLIENT_ID in GitHub Secrets"
  value       = aws_cognito_user_pool_client.main.id
}

output "cognito_domain" {
  description = "Cognito Hosted UI base URL — set as VITE_COGNITO_DOMAIN in GitHub Secrets"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "google_redirect_uri" {
  description = "Add this URI to Google OAuth App → Authorized redirect URIs"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com/oauth2/idpresponse"
}
