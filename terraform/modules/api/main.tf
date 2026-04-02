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

# ── TF-API-01: IAM role for Lambda ────────────────────────────────────────────

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "lambda" {
  name = "tracktheticket-api-lambda-role"

  # Trust policy: only the Lambda service can assume this role.
  # Without this, no one could use this role at all.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  # AWS managed policy — gives Lambda permission to write logs to CloudWatch.
  # Every Lambda needs this; without it logs won't appear in CloudWatch at all.
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  # Required when Lambda runs inside a VPC.
  # Allows Lambda to create and delete ENIs (Elastic Network Interfaces)
  # so it can communicate with RDS in the private subnet.
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  # Custom inline policy for our specific AWS resources.
  name = "tracktheticket-api-lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # S3: read and write screenshots bucket only.
        # GetObject: generate presigned URLs and serve screenshots.
        # PutObject: price-checker uploads screenshots here.
        Sid    = "S3Screenshots"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${var.screenshots_bucket_arn}/*"
      },
      {
        # Secrets Manager: read DB credentials at startup.
        # Lambda reads the secret once and caches it in memory.
        Sid    = "SecretsManager"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:tracktheticket/*"
      },
      {
        # X-Ray: send trace segments to AWS X-Ray service.
        # Required for TF-API-14 tracing to work in production.
        Sid    = "XRay"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
        ]
        Resource = "*"
      },
      {
        # ECR: pull Docker image at cold start.
        # Lambda needs to authenticate and download the image from ECR.
        Sid    = "ECRPull"
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      }
    ]
  })
}

# ── TF-API-01: Lambda function ────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  function_name = "tracktheticket-api"
  role          = aws_iam_role.lambda.arn

  # Docker image from ECR — CI/CD pushes a new image and calls
  # `aws lambda update-function-code` to point Lambda at the new digest.
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.api.repository_url}:latest"

  # Memory and timeout tuned for FastAPI + SQLAlchemy cold start.
  # 512 MB gives enough headroom; cold start is ~2-3s on first request.
  memory_size = 512
  timeout     = 30

  # Lambda runs inside the private subnet so it can reach RDS via private IP.
  # The security group controls which ports Lambda can connect to.
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  # Active tracing sends every request to X-Ray automatically.
  # Works together with aws-xray-sdk in the FastAPI app (API-14).
  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      DB_HOST              = var.db_endpoint
      DB_PORT              = "5432"
      DB_NAME              = var.db_name
      DB_USERNAME          = var.db_username
      DB_PASSWORD          = var.db_password
      AWS_REGION           = var.aws_region
      SCREENSHOTS_BUCKET   = var.screenshots_bucket_name
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
      COGNITO_REGION       = var.aws_region
    }
  }

  # Ensure IAM role and ECR image exist before creating the function
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_vpc,
    aws_iam_role_policy.lambda_custom,
    aws_ecr_repository.api,
  ]

  tags = {
    Name = "tracktheticket-api"
  }
}
