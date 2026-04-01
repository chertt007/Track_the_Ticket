variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "google_client_id" {
  description = "Google OAuth 2.0 Client ID for Cognito IdP"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth 2.0 Client Secret for Cognito IdP"
  type        = string
  sensitive   = true
}

variable "callback_urls" {
  description = "Allowed callback URLs after Cognito login (CloudFront URL)"
  type        = list(string)
}
