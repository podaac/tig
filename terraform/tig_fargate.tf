module "tig_fargate" {

  count = var.tig_fargate ? 1 : 0

  source = "./fargate"

  prefix = var.prefix
  app_name = var.app_name
  tags = var.tags
  iam_role = var.fargate_iam_role
  command = [
    "/var/lang/bin/python",
    "/var/task//podaac/lambda_handler/lambda_handler.py",
    "activity",
    "--arn",
    aws_sfn_activity.tig_ecs_task.id
  ]

  environment = {
    "PYTHONPATH": ":/var/task",
    "CONFIG_BUCKET": "${var.prefix}-internal",
    "CONFIG_DIR" : var.config_dir,
    "CONFIG_URL" : var.config_url,
    "PALETTE_URL" : var.palette_url
  }

  image = "${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}"
  ecs_cluster_arn = var.cluster_arn
  subnet_ids = var.subnet_ids
  scale_dimensions =  var.scale_dimensions != null ? var.scale_dimensions : {"ServiceName" = "${var.prefix}-${var.app_name}-fargate-service","ClusterName" = var.ecs_cluster_name}

  cpu = var.fargate_cpu
  memory = var.fargate_memory
  cluster_name = var.ecs_cluster_name

  desired_count = var.fargate_desired_count
  max_capacity = var.fargate_max_capacity
  min_capacity = var.fargate_min_capacity

  scale_up_cooldown = var.scale_up_cooldown
  scale_down_cooldown = var.scale_down_cooldown

  # Scale up settings
  comparison_operator_scale_up = var.comparison_operator_scale_up
  evaluation_periods_scale_up = var.evaluation_periods_scale_up
  metric_name_scale_up = var.metric_name_scale_up
  namespace_scale_up = var.namespace_scale_up
  period_scale_up = var.period_scale_up
  statistic_scale_up = var.statistic_scale_up
  threshold_scale_up = var.threshold_scale_up
  scale_up_step_adjustment = var.scale_up_step_adjustment

  # Scale down settings
  comparison_operator_scale_down = var.comparison_operator_scale_down
  evaluation_periods_scale_down = var.evaluation_periods_scale_down
  metric_name_scale_down = var.metric_name_scale_down
  namespace_scale_down = var.namespace_scale_down
  period_scale_down = var.period_scale_down
  statistic_scale_down = var.statistic_scale_down
  threshold_scale_down = var.threshold_scale_down
  scale_down_step_adjustment = var.scale_down_step_adjustment
}
