output "tig_task_lambda_arn"{
  value = aws_lambda_function.tig_task.arn
}

output "tig_task_lambda_arns" {
  description = "ARNs of the created tig_task Lambda functions"
  value = length(aws_lambda_function.multi_tig_task) > 1 ? [for idx in range(length(aws_lambda_function.multi_tig_task)) : aws_lambda_function.multi_tig_task[idx].arn] : length(aws_lambda_function.multi_tig_task) == 1 ? [aws_lambda_function.multi_tig_task[0].arn] : []
}

output "tig_task_lambda_arns_map" {
  description = "Map of tig Lambda function names to their ARNs"
  value = { for func in aws_lambda_function.multi_tig_task : func.function_name => func.arn }
}

output "cloudwatch_tig_task_lambda_name" {
  value = aws_cloudwatch_log_group.tig_task.name
}

output "tig_ecs_task_id" {
  value = aws_sfn_activity.tig_ecs_task.id
}

output "tig_task_cleaner_lambda_arn"{
  value = aws_lambda_function.tig_cleaner_task.arn
}
