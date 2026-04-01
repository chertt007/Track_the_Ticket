variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region — used to build the Cognito domain URL"
  type        = string
  default     = "us-east-1"
}

variable "callback_urls" {
  description = "Allowed redirect URLs after login (CloudFront URL + localhost for dev)"
  type        = list(string)
}

variable "logout_urls" {
  description = "Allowed redirect URLs after logout"
  type        = list(string)
}
