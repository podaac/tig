module "tig" {
  source = "source will be override by override.py"
  // Lambda variables
  prefix = var.prefix
  lambda_container_image_uri = "image will be override by override.py"
  role = aws_iam_role.iam_execution.arn
  cmr_environment = "UAT"
  subnet_ids = []
  security_group_ids = []
  task_logs_retention_in_days = "7"
  config_url = "https://hitide.podaac.earthdatacloud.nasa.gov/dataset-configs"
  palette_url = "https://hitide.podaac.earthdatacloud.nasa.gov/palettes"
  memory_size = 2048

  # ECS Variables
  tig_ecs = false

  # Fargate Variables
  tig_fargate = false
}
