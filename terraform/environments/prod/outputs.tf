output "frontend_url" {
  description = "Live frontend URL"
  value       = module.frontend.cloudfront_url
}

output "s3_bucket" {
  description = "Add this as S3_BUCKET in GitHub Secrets"
  value       = module.frontend.bucket_name
}

output "cloudfront_distribution_id" {
  description = "Add this as CLOUDFRONT_DISTRIBUTION_ID in GitHub Secrets"
  value       = module.frontend.cloudfront_distribution_id
}
