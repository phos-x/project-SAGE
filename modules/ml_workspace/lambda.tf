resource "aws_ecr_repository" "model_registry" {
  name                 = "${var.project_name}-${var.environment}-repo"
  image_tag_mutability = "MUTABLE"
  tags                 = local.common_tags
}

resource "aws_lambda_function" "model_server" {
  function_name = "${var.project_name}-${var.environment}-inference"
  role          = aws_iam_role.model_runner_role.arn
  
  package_type  = "Image"
  
  image_uri     = "${aws_ecr_repository.model_registry.repository_url}:latest"
  
  timeout       = 30 
  memory_size   = 2048

  environment {
    variables = {
      MODEL_BUCKET = aws_s3_bucket.ml_data.bucket
    }
  }
  tags = local.common_tags
}