locals {
  # This is the convention we use to know what belongs to each other
  ecs_resources_name = terraform.workspace == "default" ? "svc-${local.name}-${local.environment}" : "svc-${local.name}-${local.environment}-${terraform.workspace}"
}

resource "aws_sfn_activity" "tig_ecs_task" {
  name = "${local.ecs_resources_name}-ecs-activity"
  tags = merge(var.tags, { Project = var.prefix })
}

module "tig_service" {

  count = var.tig_ecs ? 1 : 0

  source = "https://github.com/nasa/cumulus/releases/download/v18.2.0/terraform-aws-cumulus-ecs-service.zip"
  prefix                                = var.prefix
  name                                  = "${local.ecs_resources_name}-ecs-task"
  tags                                  = merge(var.tags, { Project = var.prefix })
  cluster_arn                           = var.cluster_arn
  desired_count                         = var.desired_count
  image                                 = "${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}"
  log_destination_arn                   = var.log_destination_arn
  cpu                                   = var.ecs_cpu
  memory_reservation                    = var.ecs_memory_reservation

  environment = {
      CMR_ENVIRONMENT             = var.cmr_environment
      stackName                   = var.prefix
      CONFIG_BUCKET               = var.config_bucket
      CONFIG_DIR                  = var.config_dir
      LOGGING_LEVEL               = var.log_level  
      AWS_DEFAULT_REGION          = var.region
      PYTHONPATH                  = ":/var/task"
      CONFIG_URL                  = var.config_url
      PALETTE_URL                 = var.palette_url
  }

  command = [
    "/var/lang/bin/python",
    "/var/task/podaac/lambda_handler/lambda_handler.py",
    "activity",
    "--arn",
    aws_sfn_activity.tig_ecs_task.id
  ]

  alarms = {
    TaskCountHigh = {
      comparison_operator = "GreaterThanThreshold"
      evaluation_periods  = 1
      metric_name         = "MemoryUtilization"
      statistic           = "SampleCount"
      threshold           = 1
    }
  }
}
