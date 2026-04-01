# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Networking Module (TF-05)
# VPC + public/private subnets + IGW + route tables + SGs + S3 Gateway Endpoint
# No NAT Gateway — private subnets have no internet route (cost saving).
# Lambda accesses S3 via free Gateway Endpoint; RDS lives in private subnets.
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── Availability Zones ────────────────────────────────────────────────────────

data "aws_availability_zones" "available" {
  state = "available"
}

# ── VPC ───────────────────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true  # required for RDS hostname resolution
  enable_dns_support   = true

  tags = {
    Name        = "tracktheticket-${var.environment}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Internet Gateway ──────────────────────────────────────────────────────────
# Allows public subnets to reach the internet.

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "tracktheticket-${var.environment}-igw"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Public Subnets (2 AZs) ────────────────────────────────────────────────────
# CIDR: 10.0.0.0/24, 10.0.1.0/24
# Used by: ALB (future), resources that need direct internet access.

resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "tracktheticket-${var.environment}-public-${count.index + 1}"
    Type        = "public"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Private Subnets (2 AZs) ───────────────────────────────────────────────────
# CIDR: 10.0.10.0/24, 10.0.11.0/24
# Used by: RDS PostgreSQL, Lambda functions.
# No route to internet — traffic stays within VPC (or via endpoints).

resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "tracktheticket-${var.environment}-private-${count.index + 1}"
    Type        = "private"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Route Table: Public ───────────────────────────────────────────────────────
# Default route → Internet Gateway.

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "tracktheticket-${var.environment}-public-rt"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ── Route Table: Private ──────────────────────────────────────────────────────
# No default internet route — intentionally offline (no NAT Gateway).
# S3 Gateway Endpoint adds its own routes automatically (see below).

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "tracktheticket-${var.environment}-private-rt"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ── S3 Gateway Endpoint ───────────────────────────────────────────────────────
# FREE — Lambda can read/write S3 (screenshots) without internet.
# Gateway endpoints inject routes directly into route tables — no cost per request.

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.private.id,
    aws_route_table.public.id,
  ]

  tags = {
    Name        = "tracktheticket-${var.environment}-s3-endpoint"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Security Group: Lambda ────────────────────────────────────────────────────
# Applied to all Lambda functions placed inside the VPC.
# No inbound — Lambda is invoked by AWS internally, not over the network.
# Outbound all — allows RDS (port 5432), S3 via endpoint, SQS, SSM.

resource "aws_security_group" "lambda" {
  name        = "tracktheticket-${var.environment}-lambda-sg"
  description = "Lambda functions - outbound access to RDS and AWS services"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "tracktheticket-${var.environment}-lambda-sg"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Security Group: RDS ───────────────────────────────────────────────────────
# Only allows PostgreSQL connections from Lambda — nothing else.

resource "aws_security_group" "rds" {
  name        = "tracktheticket-${var.environment}-rds-sg"
  description = "RDS PostgreSQL - inbound only from Lambda security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  tags = {
    Name        = "tracktheticket-${var.environment}-rds-sg"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
