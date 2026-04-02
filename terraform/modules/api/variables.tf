variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
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

variable "screenshots_bucket_name" {
  description = "Screenshots S3 bucket name — used in Lambda env vars"
  type        = string
}

variable "screenshots_bucket_arn" {
  description = "Screenshots S3 bucket ARN — added to Lambda IAM policy"
  type        = string
}

variable "aws_region" {
  description = "AWS region for Lambda environment variables"
  type        = string
  default     = "us-east-1"
}
