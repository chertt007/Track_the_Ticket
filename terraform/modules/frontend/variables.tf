variable "bucket_name" {
  description = "S3 bucket name for the frontend static files (must be globally unique)"
  type        = string
}

variable "screenshots_bucket_name" {
  description = "S3 bucket name for price-check screenshots (must be globally unique)"
  type        = string
}

variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}
