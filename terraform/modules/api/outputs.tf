# ── ECR ───────────────────────────────────────────────────────────────────────

output "ecr_repository_url" {
  description = "ECR repository URL — used by CI/CD to push Docker images"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name — used in GitHub Actions docker/push step"
  value       = aws_ecr_repository.api.name
}

# ── Lambda + API Gateway — populated in TF-API-01 / TF-API-03 ─────────────────

# output "api_endpoint" {
#   description = "API Gateway HTTP endpoint URL"
#   value       = aws_apigatewayv2_api.api.api_endpoint
# }

# output "lambda_function_name" {
#   description = "Lambda function name — used by CI/CD for update-function-code"
#   value       = aws_lambda_function.api.function_name
# }

# output "lambda_role_arn" {
#   description = "Lambda IAM role ARN"
#   value       = aws_iam_role.lambda.arn
# }
