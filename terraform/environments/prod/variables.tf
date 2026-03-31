variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend (must be globally unique across all AWS)"
  type        = string
  default     = "tracktheticket-frontend-prod"
}
