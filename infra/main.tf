terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# IAM role for the Lambda function
# ---------------------------------------------------------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Read-only access to the S3 bucket holding the vector index
resource "aws_iam_role_policy" "s3_read_index" {
  name = "${var.project_name}-s3-read-index"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.index_bucket.arn}/*"
    }]
  })
}

# ---------------------------------------------------------------------------
# S3 bucket for the FAISS index artifact
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "index_bucket" {
  bucket = "${var.project_name}-vector-index-${var.environment}"
}

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "rag_chatbot" {
  function_name = "${var.project_name}-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 512

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  environment {
    variables = {
      LOG_LEVEL         = "INFO"
      LLM_MODEL         = var.llm_model
      LLM_TEMPERATURE   = "0.2"
      LLM_MAX_TOKENS    = "800"
      TOP_K             = "4"
      VECTOR_INDEX_PATH = "/tmp/faiss_index"
      ANTHROPIC_API_KEY = var.anthropic_api_key
    }
  }
}

# ---------------------------------------------------------------------------
# API Gateway (HTTP API) in front of the Lambda
# ---------------------------------------------------------------------------
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.rag_chatbot.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag_chatbot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
