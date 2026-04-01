output "db_endpoint" {
  description = "RDS hostname (without port) — use as DB_HOST in Lambda env vars"
  value       = aws_db_instance.main.address
}

output "db_port" {
  description = "RDS port (5432)"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "PostgreSQL database name"
  value       = aws_db_instance.main.db_name
}

output "db_connection_string" {
  description = "Full PostgreSQL connection string (sensitive) — for reference only"
  value       = "postgresql://${var.db_username}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}"
  sensitive   = true
}

output "secrets_manager_arn" {
  description = "ARN of the Secrets Manager secret — add to Lambda IAM policy (secretsmanager:GetSecretValue)"
  value       = aws_secretsmanager_secret.db.arn
}
