variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
  default     = "prod"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "tracktheticket"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the RDS subnet group"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group ID for RDS — allows access from Lambda SG only"
  type        = string
}
