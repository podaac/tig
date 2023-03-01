variable region{
  description = "aws region"
  type = string
  default = "us-west-2"
}

variable app_name{
  description = "app name"
  type = string
}

variable prefix{
  description = "prefix to aws resources"
  type = string
  default = ""
}

variable "tags" {
  description = "Tags to be applied to Cumulus resources that support tags"
  type        = map(string)
  default     = {}
}

variable "command" {
  description = "command to run for ECS task"
  type = list
}

variable "environment" {
  description = "Environment variables to pass to the ECS container"
  type    = map(string)
  default = {}
}

variable iam_role{
  description = "iam role for run a fargate ECS task"
  type = string
}

variable image{
  description = "image for ECS task"
  type = string
}

variable ecs_cluster_arn{
  description = "cluster to run fargate tasks in"
  type = string
}

variable subnet_ids{
  type = list
}

variable scale_dimensions{
  type = map(string)
}

variable cpu{
  description = "cluster to run fargate tasks in"
  type = number
}

variable memory {
  description = ""
  type = number
}

variable ephemeralStorageSize{
  description = ""
  type = number
  default = 20
}

variable cluster_name{
  description = ""
  type = string
}

variable desired_count {
  description = ""
  type = number
}

variable min_capacity {
  description = ""
  type = number
}

variable max_capacity {
  description = ""
  type = number
}

variable scale_down_cooldown{
  description = ""
  type = number
}

variable scale_up_cooldown{
  description = ""
  type = number
}

#Scale up variables
variable comparison_operator_scale_up{
  description = "The arithmetic operation to use when comparing the specified Statistic and Threshold"
  type = string
}

variable evaluation_periods_scale_up{
  description = "The number of periods over which data is compared to the specified threshold"
  type = number
}

variable metric_name_scale_up{
  description = "name of the metric"
  type = string
}

variable namespace_scale_up{
  description = "namespace for the alarm's associated metric"
  type = string
}

variable period_scale_up{
  description = "period in seconds over which the specified statistic is applied"
  type = number
}

variable statistic_scale_up{
  description = "statistic to apply to the metric"
  type = string
}

variable threshold_scale_up{
  description = "threshold for statistic to compare against to trigger step"
  type = number
}

# use "" to indicate infinity
variable "scale_up_step_adjustment" {
  description = "step adjustment to make when scaling up fargate"
  type        = list(object({ metric_interval_lower_bound = string, metric_interval_upper_bound = string, scaling_adjustment = string }))
  default     = []
}

#Scale down variables
variable comparison_operator_scale_down{
  description = "The arithmetic operation to use when comparing the specified Statistic and Threshold"
  type = string
}

variable evaluation_periods_scale_down{
  description = "The number of periods over which data is compared to the specified threshold"
  type = number
}

variable metric_name_scale_down{
  description = "name of the metric"
  type = string
}

variable namespace_scale_down{
  description = "namespace for the alarm's associated metric"
  type = string
}

variable period_scale_down{
  description = "period in seconds over which the specified statistic is applied"
  type = number
}

variable statistic_scale_down{
  description = "statistic to apply to the metric"
  type = string
}

variable threshold_scale_down{
  description = "threshold for statistic to compare against to trigger step"
  type = number
}

# use "" to indicate infinity
variable "scale_down_step_adjustment" {
  description = "step adjustment to make when scaling down fargate"
  type        = list(object({ metric_interval_lower_bound = string, metric_interval_upper_bound = string, scaling_adjustment = string }))
  default     = []
}