# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Frontend Infrastructure
# S3 (private) + CloudFront OAC + bucket policy
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── S3 Bucket ─────────────────────────────────────────────────────────────────

resource "aws_s3_bucket" "frontend" {
  bucket = var.bucket_name

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Block all public access — CloudFront reads via OAC, not public URLs
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for rollback capability
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ── CloudFront Origin Access Control ─────────────────────────────────────────

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.bucket_name}-oac"
  description                       = "OAC for Track the Ticket frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ── CloudFront Distribution ───────────────────────────────────────────────────

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "Track the Ticket frontend"
  price_class         = "PriceClass_100" # US + Europe — good for Israel

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${var.bucket_name}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Cache HTML for 0s (always fresh), assets for 1 year (they have hashed names)
    cache_policy_id = aws_cloudfront_cache_policy.frontend.id
  }

  # React Router: serve index.html for all unknown paths (SPA fallback)
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
  }
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project     = "TrackTheTicket"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Cache Policy ──────────────────────────────────────────────────────────────

resource "aws_cloudfront_cache_policy" "frontend" {
  name        = "${var.bucket_name}-cache-policy"
  min_ttl     = 0
  default_ttl = 0      # HTML — no cache by default
  max_ttl     = 31536000 # Hashed assets can be cached up to 1 year

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config  { cookie_behavior = "none" }
    headers_config  { header_behavior = "none" }
    query_strings_config { query_string_behavior = "none" }
    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

# ── S3 Bucket Policy — allow CloudFront OAC only ──────────────────────────────

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
