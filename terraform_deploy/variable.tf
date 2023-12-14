variable prefix{
  description = "prefix to aws resources"
  type = string
  default = ""
}

variable region{
  description = "aws region"
  type = string
  default = "us-west-2"
}

variable "profile" {
  type    = string
  default = null
}

variable "cma_version" {
  type    = string
  default = "v2.0.3"
}

variable "app_name" {
  default = "forge"
}

variable "default_tags" {
  type = map(string)
  default = {}
}

variable "stage" {}
variable "app_version" {}
