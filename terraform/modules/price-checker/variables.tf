variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "db_endpoint" {
  description = "RDS endpoint"
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

variable "screenshots_bucket_name" {
  description = "S3 bucket name for screenshots"
  type        = string
}

variable "screenshots_bucket_arn" {
  description = "S3 bucket ARN for screenshots (used in IAM policy)"
  type        = string
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for the browser-use agent (google/gemini-2.5-flash)"
  type        = string
  sensitive   = true
}

variable "langfuse_public_key" {
  description = "Langfuse public key for LLM tracing"
  type        = string
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for LLM tracing"
  type        = string
  sensitive   = true
  default     = ""
}
