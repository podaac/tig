locals {
  # This is the convention we use to know what belongs to each other
  lambda_resources_name = terraform.workspace == "default" ? "svc-${local.name}-${local.environment}" : "svc-${local.name}-${local.environment}-${terraform.workspace}"
}

resource "aws_lambda_function" "tig_task" {

  depends_on = [
    null_resource.upload_ecr_image
  ]

  function_name = "${local.lambda_resources_name}-lambda"
  image_uri     = "${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}"
  role          = var.role
  timeout       = var.timeout
  memory_size   = var.memory_size
  package_type  = "Image"
  
  image_config {
    command = var.command
    entry_point = var.entry_point
    working_directory = var.working_directory
  }

  environment {
    variables = {
      CMR_ENVIRONMENT             = var.cmr_environment
      stackName                   = var.prefix
      CONFIG_BUCKET               = var.config_bucket
      CONFIG_DIR                  = var.config_dir
      LOGGING_LEVEL               = var.log_level
      CONFIG_URL                  = var.config_url
      PALETTE_URL                 = var.palette_url
    }
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = merge(var.tags, { Project = var.prefix })
}

resource "aws_cloudwatch_log_group" "tig_task" {
  name              = "/aws/lambda/${aws_lambda_function.tig_task.function_name}"
  retention_in_days = var.task_logs_retention_in_days
  tags              = merge(var.tags, { Project = var.prefix })
}


resource "aws_lambda_function" "tig_cleaner_task" {

  depends_on = [
    null_resource.upload_ecr_image
  ]
  
  function_name = "${local.lambda_resources_name}-lambda-cleaner"
  image_uri     = "${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}"
  role          = var.role
  timeout       = var.timeout
  memory_size   = var.memory_size
  package_type  = "Image"
  
  architectures = var.architectures

  image_config {
    command = ["podaac.lambda_handler.clean_lambda_handler.handler"]
    entry_point = var.entry_point
    working_directory = var.working_directory
  }

  environment {
    variables = {
      CMR_ENVIRONMENT             = var.cmr_environment
      stackName                   = var.prefix
      CONFIG_BUCKET               = var.config_bucket
      CONFIG_DIR                  = var.config_dir
      LOGGING_LEVEL               = var.log_level
      CONFIG_URL                  = var.config_url
      PALETTE_URL                 = var.palette_url
    }
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = merge(var.tags, { Project = var.prefix })
}