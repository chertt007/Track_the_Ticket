# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Database Module
# RDS PostgreSQL 16 | db.t3.micro | 20 GB gp2 | publicly accessible (dev only)
# ─────────────────────────────────────────────────────────────────────────────

# ── Dev public-access security group ─────────────────────────────────────────
# WARNING: port 5432 open to 0.0.0.0/0 for DataGrip/DBeaver access during dev.
# Remove before production — see task SEC-01 in kanban.

resource "aws_security_group" "rds_dev_access" {
  name        = "tracktheticket-rds-dev-${var.environment}"
  description = "Dev only - port 5432 open to all IPs. Remove before production (SEC-01)"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL dev access from all IPs - close before production (SEC-01)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "tracktheticket-rds-dev-${var.environment}"
  }
}

# ── RDS subnet group ──────────────────────────────────────────────────────────
# Uses public subnets because publicly_accessible = true requires internet routing.
# Lambda in private subnets can still reach RDS via VPC internal routing.

resource "aws_db_subnet_group" "main" {
  name        = "tracktheticket-${var.environment}"
  description = "TrackTheTicket RDS subnet group"
  subnet_ids  = var.subnet_ids

  tags = {
    Name = "tracktheticket-${var.environment}"
  }
}

# ── Secrets Manager: store DB connection credentials ─────────────────────────
# Lambda reads this secret at startup to get the DB password.
# recovery_window_in_days = 0 means the secret is deleted immediately on destroy
# (no 30-day recovery window), so terraform destroy completes cleanly.

resource "aws_secretsmanager_secret" "db" {
  name                    = "tracktheticket/rds/credentials"
  description             = "RDS PostgreSQL connection credentials for TrackTheTicket"
  recovery_window_in_days = 0

  tags = {
    Name = "tracktheticket-rds-credentials-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  # Store all connection details as JSON so Lambda can parse with a single API call
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = var.db_name
  })
}

# ── RDS instance ──────────────────────────────────────────────────────────────

resource "aws_db_instance" "main" {
  identifier = "tracktheticket-${var.environment}"

  # Engine
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class

  # Storage — gp2, starts at 20 GB, auto-scales up to 100 GB if needed
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  # Credentials
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Network
  # Two SGs attached:
  #   1. rds_security_group_id (from networking) — allows Lambda on 5432
  #   2. rds_dev_access — allows all IPs on 5432 for DataGrip/DBeaver (dev only)
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_security_group_id, aws_security_group.rds_dev_access.id]
  publicly_accessible    = true # Dev only — set to false before production (SEC-01)

  # Backup — 2 days retention, runs at 03:00-04:00 UTC
  backup_retention_period = 2
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Lifecycle — fast deletion, no snapshot, no protection
  skip_final_snapshot = true  # No snapshot on destroy
  deletion_protection = false # Allow instant terraform destroy
  multi_az            = false # Single AZ — enable when real users appear

  # Performance Insights free tier only covers db.t3.medium and above
  performance_insights_enabled = false

  tags = {
    Name = "tracktheticket-${var.environment}"
  }
}
