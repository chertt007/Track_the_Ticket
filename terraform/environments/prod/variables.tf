variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend static files (must be globally unique across all AWS)"
  type        = string
  default     = "tracktheticket-frontend-prod"
}

variable "screenshots_bucket_name" {
  description = "S3 bucket name for price-check screenshots (must be globally unique across all AWS)"
  type        = string
  default     = "tracktheticket-screenshots-prod"
}

# ── Variables added as modules are implemented ────────────────────────────────

# variable "google_client_id" {
#   description = "Google OAuth 2.0 Client ID (from GCP Console)"
#   type        = string
#   sensitive   = true
# }

# variable "google_client_secret" {
#   description = "Google OAuth 2.0 Client Secret (from GCP Console)"
#   type        = string
#   sensitive   = true
# }

# variable "db_username" {
#   description = "RDS PostgreSQL master username"
#   type        = string
#   sensitive   = true
# }

# variable "db_password" {
#   description = "RDS PostgreSQL master password"
#   type        = string
#   sensitive   = true
# }

# variable "ecr_image_uri" {
#   description = "API Lambda ECR image URI — injected by CI/CD on deploy"
#   type        = string
# }
