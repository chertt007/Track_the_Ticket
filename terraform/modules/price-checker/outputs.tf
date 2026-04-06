output "queue_url" {
  description = "SQS queue URL — set as PRICE_CHECKER_QUEUE_URL in API Lambda env vars"
  value       = aws_sqs_queue.price_checker.url
}

output "queue_arn" {
  description = "SQS queue ARN — used in API Lambda IAM policy for sqs:SendMessage"
  value       = aws_sqs_queue.price_checker.arn
}

output "lambda_function_name" {
  description = "Price-checker Lambda function name"
  value       = aws_lambda_function.price_checker.function_name
}

output "ecr_repository_url" {
  description = "ECR repository URL — used by deploy-price-checker CI/CD"
  value       = aws_ecr_repository.price_checker.repository_url
}
