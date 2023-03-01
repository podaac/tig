variable app_name{
  description = "app name"
  default = "tig"
  type = string
}

variable image{
  description = "ECR image arn"
  type = string
}

variable role{
  description = "role for lambda"
  type = string
}

variable timeout{
  description = "Lambda function timeout"
  type = number
  default = 600
}

variable memory_size{
  description = "Lambda memory size"
  type = number
  default = 1024
}

variable command{
  description = "Command to run for docker container"
  type = list(string)
  default = ["podaac.lambda_handler.lambda_handler.handler"]
}

variable entry_point{
  description = "Entry point for docker container"
  type = list(string)
  default = ["/usr/local/bin/python", "-m", "awslambdaric"]
}

variable working_directory{
  description = "Working directory for docker container"
  type = string
  default = "/function"
}

variable cmr_environment{
  description = "cmr environment"
  type = string
  default = ""
}

variable prefix{
  description = "prefix to aws resources"
  type = string
  default = ""
}

variable subnet_ids{
  description = "subnet id for lambda function"
  type = list(string)
}

variable security_group_ids{
  description = "security group for lambda"
  type = list(string)
}

variable tags{
  description = "tags"
  type = map(string)
  default = {}
}

variable task_logs_retention_in_days{
  description = "Log retention days"
  type = number
  default = 30
}

variable config_bucket{
  description = "Bucket where image configuration files are"
  type = string
  default = null
}

variable config_dir{
  description = "directory of the configuration files in a bucket"
  type = string
  default = null
}

variable config_url{
  description = "the url of where to retrieve configurations"
  type = string
  default = null
}

variable palette_url{
  description = "the url of where to retrieve palettes"
  type = string
  default = null
}

variable log_level{
  description = "log level of cumulus logger"
  type = string
  default = "info"
}

# ECS ACTIVITY VARIABLES

variable cluster_arn{
  description = "cumulus cluster arn"
  type = string
  default = ""
}

variable desired_count{
  description = "number of ecs tig task to run"
  type = number
  default = 1
}

variable "log_destination_arn" {
  type        = string
  default     = null
  description = "A shared AWS:Log:Destination that receives logs in log_groups"
}

variable ecs_cpu{
  description = "cpu unit to allocate to a tig task"
  type = number
  default = 700
}

variable ecs_memory_reservation{
  description = "memory unit to allocate to tig task"
  type = number
  default = 1024
}

variable region{
  description = "aws region"
  type = string
  default = "us-west-2"
}

# FARGATE variables

variable fargate_iam_role{
  description = "iam role to use for a fargate task"
  type = string
  default = ""
}

variable ecs_cluster_name{
  description = "cluster where fargate task will be deployed"
  type = string
  default = ""
}

variable tig_fargate{
  description = "boolean to deploy fargate task"
  type = bool
  default = false
}

variable tig_ecs{
  description = "boolean to deploy ecs task"
  type = bool
  default = false
}

variable fargate_memory{
  description = "amount of memory to allocate for a single fargate task"
  type = number
  default = 2048
}

variable fargate_cpu{
  description = "amount of cpu to allocate for a single fargate task"
  type = number
  default = 1024
}

variable fargate_desired_count{
  description = "desired count of how many fargate task"
  type = number
  default = 1
}

variable fargate_min_capacity{
  description = "minimum number of fargate task when scaling"
  type = number
  default = 1
}

variable fargate_max_capacity{
  description = "maximum number of fargate task when scaling"
  type = number
  default = 10
}

variable scale_dimensions{
  description = "cloudwatch dimensions to scale on"
  type = map(string)
  default = null
}

variable scale_up_cooldown{
  description = "seconds before able to scaling up again"
  type = number
  default = 60
}

variable scale_down_cooldown{
  description = "seconds before able to scaling down again"
  type = number
  default = 120
}

variable comparison_operator_scale_up{
  description = "The arithmetic operation to use when comparing the specified Statistic and Threshold"
  type = string
  default = "GreaterThanOrEqualToThreshold"
}

variable evaluation_periods_scale_up{
  description = "The number of periods over which data is compared to the specified threshold"
  type = number
  default = 1
}

variable metric_name_scale_up{
  description = "name of the metric"
  type = string
  default = "CPUUtilization"
}

variable namespace_scale_up{
  description = "namespace for the alarm's associated metric"
  type = string
  default = "AWS/ECS"
}

variable period_scale_up{
  description = "period in seconds over which the specified statistic is applied"
  type = number
  default = 60
}

variable statistic_scale_up{
  description = "statistic to apply to the metric"
  type = string
  default = "Average"
}

variable threshold_scale_up{
  description = "threshold for statistic to compare against to trigger step"
  type = number
  default = 50
}

variable scale_up_step_adjustment{
  description = "step adjustment to make when scaling up fargate"
  type = list
  default = [
    {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = ""
      scaling_adjustment = 1
    }
  ]
}

variable comparison_operator_scale_down{
  description = "The arithmetic operation to use when comparing the specified Statistic and Threshold"
  type = string
  default = "LessThanOrEqualToThreshold"
}

variable evaluation_periods_scale_down{
  description = "The number of periods over which data is compared to the specified threshold"
  type = number
  default = 1
}

variable metric_name_scale_down{
  description = "name of the metric"
  type = string
  default = "CPUUtilization"
}

variable namespace_scale_down{
  description = "namespace for the alarm's associated metric"
  type = string
  default = "AWS/ECS"
}

variable period_scale_down{
  description = "period in seconds over which the specified statistic is applied"
  type = number
  default = 60
}

variable statistic_scale_down{
  description = "statistic to apply to the metric"
  type = string
  default = "Average"
}

variable threshold_scale_down{
  description = "threshold for statistic to compare against to trigger step"
  type = number
  default = 50
}

# use "" to indicate infinity
variable "scale_down_step_adjustment" {
  description = "step adjustment to make when scaling down fargate"
  type = list
  default = [
    {
      metric_interval_lower_bound = ""
      metric_interval_upper_bound = 0
      scaling_adjustment = -1
    },
    {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = ""
      scaling_adjustment = 0
    }
  ]
}
