output "bucket_name" {
  description = "S3 bucket name — set as S3_BUCKET in GitHub Secrets"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID — set as CLOUDFRONT_DISTRIBUTION_ID in GitHub Secrets"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_url" {
  description = "Public URL of the frontend"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
