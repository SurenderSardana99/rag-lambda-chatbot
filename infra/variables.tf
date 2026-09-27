variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "rag-chatbot"
}

variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "lambda_package_path" {
  description = "Path to the zipped Lambda deployment package"
  type        = string
  default     = "../build/lambda_package.zip"
}

variable "llm_model" {
  description = "LLM model identifier to use for generation"
  type        = string
  default     = "claude-sonnet-4-6"
}

variable "anthropic_api_key" {
  description = "Anthropic API key (pass via -var or TF_VAR_ env var, never commit)"
  type        = string
  sensitive   = true
}
