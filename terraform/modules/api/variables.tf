variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "ecr_image_uri" {
  description = "ECR image URI for the API Lambda (injected by CI/CD)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Lambda VPC config"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Lambda VPC config"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda"
  type        = string
}

variable "db_endpoint" {
  description = "RDS endpoint for DATABASE_URL env var"
  type        = string
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
}

variable "db_username" {
  description = "PostgreSQL username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for JWT validation"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito App Client ID for JWT validation"
  type        = string
}

variable "screenshots_bucket_arn" {
  description = "Screenshots S3 bucket ARN — added to Lambda IAM policy"
  type        = string
}
