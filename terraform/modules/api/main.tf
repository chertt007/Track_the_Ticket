# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — API Module
# ECR repository + Lambda Docker + API Gateway HTTP v2 + IAM role
# ─────────────────────────────────────────────────────────────────────────────

# ── TF-API-02: ECR repository ─────────────────────────────────────────────────

resource "aws_ecr_repository" "api" {
  # Repository name — Docker images are pushed here by CI/CD.
  # Full URI: {account_id}.dkr.ecr.{region}.amazonaws.com/tracktheticket-api
  name                 = "tracktheticket-api"
  image_tag_mutability = "MUTABLE" # allows overwriting the "latest" tag on each deploy

  image_scanning_configuration {
    # Automatically scans pushed images for known CVEs — free, no reason to skip
    scan_on_push = true
  }

  tags = {
    Name = "tracktheticket-api"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  # Keeps only the 10 most recent images — prevents unbounded storage costs.
  # Older images are deleted automatically.
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the 10 most recent images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
