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

variable "db_username" {
  description = "RDS PostgreSQL master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS PostgreSQL master password (min 8 chars)"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for price-checker Lambda (google/gemini-2.5-flash)"
  type        = string
  sensitive   = true
}

variable "langfuse_public_key" {
  description = "Langfuse public key for LLM tracing"
  type        = string
  default     = "pk-lf-1f60a6e6-26f7-46dc-9cab-cf7940f51b7d"
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for LLM tracing"
  type        = string
  sensitive   = true
  default     = "sk-lf-9746e12d-2b7f-4ac4-887f-a3055f737344"
}

