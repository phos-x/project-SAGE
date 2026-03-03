resource "aws_s3_bucket" "ml_data" {
  bucket = "${var.project_name}-${var.environment}-ml-data"
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ml_data_encryption" {
  bucket = aws_s3_bucket.ml_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
