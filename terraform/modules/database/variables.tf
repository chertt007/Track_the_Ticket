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
  description = "PostgreSQL master password (min 8 chars, store in terraform.tfvars)"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "VPC ID — used for the dev public-access security group"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the RDS subnet group (public subnets while publicly_accessible = true)"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group from networking module — allows inbound 5432 from Lambda SG"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}
