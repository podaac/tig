output "tig_task_lambda_arn"{
  value = aws_lambda_function.tig_task.arn
}

output "cloudwatch_tig_task_lambda_name" {
  value = aws_cloudwatch_log_group.tig_task.name
}

output "tig_ecs_task_id" {
  value = aws_sfn_activity.tig_ecs_task.id
}
