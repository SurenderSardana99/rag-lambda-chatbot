output "api_endpoint" {
  description = "Invoke URL for the chat endpoint"
  value       = "${aws_apigatewayv2_stage.default.invoke_url}/chat"
}

output "lambda_function_name" {
  value = aws_lambda_function.rag_chatbot.function_name
}

output "index_bucket_name" {
  value = aws_s3_bucket.index_bucket.bucket
}
