resource "aws_cloudwatch_log_group" "fargate_cloudwatch_log_group" {
  name              = "${var.prefix}-${var.app_name}-fargate-EcsLogs"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.prefix}-${var.app_name}-fargate"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.iam_role
  task_role_arn            = var.iam_role

  container_definitions = jsonencode([
    {
      name              = "${var.prefix}-${var.app_name}-fargate"
      cpu               = var.cpu
      essential         = true
      image             = var.image
      memoryReservation = var.memory

      environment       = [for k, v in var.environment : { name = k, value = v }]
      command = var.command
      ephemeralStorage = var.ephemeralStorageSize

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group  = aws_cloudwatch_log_group.fargate_cloudwatch_log_group.name
          awslogs-region = var.region
          awslogs-stream-prefix = "container"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "fargate_ecs_service" {
  name            = "${var.prefix}-${var.app_name}-fargate-service"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    assign_public_ip = false
  }
}

resource "aws_appautoscaling_target" "fargate_ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.cluster_name}/${aws_ecs_service.fargate_ecs_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "fargate_scale_down" {
  name               = "${var.prefix}-${var.app_name}-fargate-policy-scale-down"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.fargate_ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.fargate_ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.fargate_ecs_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = var.scale_down_cooldown
    metric_aggregation_type = "Average"

    dynamic "step_adjustment" {
      for_each = var.scale_down_step_adjustment
      content {
        metric_interval_lower_bound = lookup(step_adjustment.value, "metric_interval_lower_bound")
        metric_interval_upper_bound = lookup(step_adjustment.value, "metric_interval_upper_bound")
        scaling_adjustment          = lookup(step_adjustment.value, "scaling_adjustment")
      }
    }
  }
}

resource "aws_appautoscaling_policy" "fargate_scale_up" {
  name               = "${var.prefix}-${var.app_name}-fargate-policy-scale-up"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.fargate_ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.fargate_ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.fargate_ecs_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = var.scale_up_cooldown
    metric_aggregation_type = "Average"

    dynamic "step_adjustment" {
      for_each = var.scale_up_step_adjustment
      content {
        metric_interval_lower_bound = lookup(step_adjustment.value, "metric_interval_lower_bound")
        metric_interval_upper_bound = lookup(step_adjustment.value, "metric_interval_upper_bound")
        scaling_adjustment          = lookup(step_adjustment.value, "scaling_adjustment")
      }
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "scale_up" {
  alarm_name                = "${var.prefix}-${var.app_name}-fargate-alarm-scale-up"
  comparison_operator       = var.comparison_operator_scale_up
  evaluation_periods        = var.evaluation_periods_scale_up
  metric_name               = var.metric_name_scale_up
  namespace                 = var.namespace_scale_up
  period                    = var.period_scale_up
  statistic                 = var.statistic_scale_up
  threshold                 = var.threshold_scale_up
  alarm_description         = "This metric monitors ECS Cluster fargate task going up"
  alarm_actions             = [aws_appautoscaling_policy.fargate_scale_up.arn]
  dimensions                = var.scale_dimensions
}

resource "aws_cloudwatch_metric_alarm" "scale_down" {
  alarm_name                = "${var.prefix}-${var.app_name}-fargate-alarm-scale-down"
  comparison_operator       = var.comparison_operator_scale_down
  evaluation_periods        = var.evaluation_periods_scale_down
  metric_name               = var.metric_name_scale_down
  namespace                 = var.namespace_scale_down
  period                    = var.period_scale_down
  statistic                 = var.statistic_scale_down
  threshold                 = var.threshold_scale_down
  alarm_description         = "This metric monitors ECS Cluster fargate task going down"
  alarm_actions             = [aws_appautoscaling_policy.fargate_scale_down.arn]
  dimensions                = var.scale_dimensions
}

