resource "aws_apigatewayv2_api" "ml_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  target        = aws_lambda_function.model_server.arn
  tags          = local.common_tags
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.model_server.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ml_api.execution_arn}/*/*"
}

output "api_endpoint" {
  value       = aws_apigatewayv2_api.ml_api.api_endpoint
  description = "The public URL to send JSON features for predictions."
}