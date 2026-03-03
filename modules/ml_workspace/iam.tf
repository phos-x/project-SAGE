resource "aws_iam_role" "model_runner_role" {
  name = "${var.project_name}-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "s3_read_policy" {
  name = "${var.project_name}-s3-read"
  role = aws_iam_role.model_runner_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Effect   = "Allow"
      Resource = [
        aws_s3_bucket.ml_data.arn,
        "${aws_s3_bucket.ml_data.arn}/*"
      ]
    }]
  })
}
