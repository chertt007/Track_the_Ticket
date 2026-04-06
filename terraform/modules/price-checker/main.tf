# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Price-Checker Module
# ECR repository + Lambda Docker (1024 MB / 300s) + SQS queue + EventBridge cron
# IAM: Lambda reads SQS, writes S3 screenshots, logs to CloudWatch
# ─────────────────────────────────────────────────────────────────────────────

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ── ECR repository ────────────────────────────────────────────────────────────

resource "aws_ecr_repository" "price_checker" {
  name                 = "tracktheticket-price-checker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "tracktheticket-price-checker" }
}

resource "aws_ecr_lifecycle_policy" "price_checker" {
  repository = aws_ecr_repository.price_checker.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 10 most recent images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ── SQS queue + Dead Letter Queue ─────────────────────────────────────────────

resource "aws_sqs_queue" "price_checker_dlq" {
  name                      = "tracktheticket-price-checker-dlq"
  message_retention_seconds = 1209600 # 14 days — enough time to inspect failures

  tags = { Name = "tracktheticket-price-checker-dlq" }
}

resource "aws_sqs_queue" "price_checker" {
  name = "tracktheticket-price-checker"

  # Price check takes up to 90s; allow 3 attempts before going to DLQ.
  # visibility_timeout must be >= Lambda timeout to avoid double-processing.
  visibility_timeout_seconds = 360  # 6 min (Lambda timeout 300s + buffer)
  message_retention_seconds  = 86400 # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.price_checker_dlq.arn
    maxReceiveCount     = 3
  })

  tags = { Name = "tracktheticket-price-checker" }
}

# ── IAM role for the price-checker Lambda ─────────────────────────────────────

resource "aws_iam_role" "price_checker" {
  name = "tracktheticket-price-checker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "price_checker_basic" {
  role       = aws_iam_role.price_checker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "price_checker_custom" {
  name = "tracktheticket-price-checker-policy"
  role = aws_iam_role.price_checker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSConsume"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = aws_sqs_queue.price_checker.arn
      },
      {
        Sid    = "S3Screenshots"
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:GetObject"]
        Resource = "${var.screenshots_bucket_arn}/*"
      },
      {
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

# ── Lambda function ───────────────────────────────────────────────────────────

resource "aws_lambda_function" "price_checker" {
  function_name = "tracktheticket-price-checker"
  role          = aws_iam_role.price_checker.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.price_checker.repository_url}:latest"

  # browser-use + Playwright needs plenty of memory; 300s for the full agent run
  memory_size = 1024
  timeout     = 300

  environment {
    variables = {
      DB_HOST              = var.db_endpoint
      DB_PORT              = "5432"
      DB_NAME              = var.db_name
      DB_USERNAME          = var.db_username
      DB_PASSWORD          = var.db_password
      SCREENSHOTS_BUCKET   = var.screenshots_bucket_name
      OPENROUTER_API_KEY   = var.openrouter_api_key
      PRICE_CHECKER_MODEL  = "google/gemini-2.5-flash"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.price_checker_basic,
    aws_iam_role_policy.price_checker_custom,
    aws_ecr_repository.price_checker,
  ]

  # image_uri is managed by the deploy-price-checker GitHub Actions workflow.
  # Ignore changes here so Terraform doesn't revert to :latest after a real deploy.
  lifecycle {
    ignore_changes = [image_uri]
  }

  tags = { Name = "tracktheticket-price-checker" }
}

# ── SQS → Lambda event source mapping ────────────────────────────────────────

resource "aws_lambda_event_source_mapping" "sqs_to_price_checker" {
  event_source_arn = aws_sqs_queue.price_checker.arn
  function_name    = aws_lambda_function.price_checker.arn

  # Process one subscription at a time (browser-use is resource-intensive)
  batch_size = 1

  # Retry on failure — message goes back to queue, then to DLQ after max attempts
  function_response_types = ["ReportBatchItemFailures"]
}

# ── EventBridge cron: 08:00, 16:00, 21:00 Israel time (UTC+3) ─────────────────

resource "aws_cloudwatch_event_rule" "price_checker_cron" {
  name                = "tracktheticket-price-checker-cron"
  description         = "Run price checker 3x/day at 05:00, 13:00, 18:00 UTC (= 08:00, 16:00, 21:00 IST)"
  schedule_expression = "cron(0 5,13,18 * * ? *)"

  tags = { Name = "tracktheticket-price-checker-cron" }
}

resource "aws_cloudwatch_event_target" "price_checker_cron" {
  rule      = aws_cloudwatch_event_rule.price_checker_cron.name
  target_id = "PriceCheckerLambda"
  arn       = aws_lambda_function.price_checker.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.price_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.price_checker_cron.arn
}

# ── CloudWatch log group ──────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "price_checker" {
  name              = "/aws/lambda/tracktheticket-price-checker"
  retention_in_days = 14

  tags = { Name = "tracktheticket-price-checker-logs" }
}
