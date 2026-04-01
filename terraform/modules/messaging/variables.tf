variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "price_checker_lambda_arn" {
  description = "ARN of the price-checker Lambda triggered by SQS"
  type        = string
}
