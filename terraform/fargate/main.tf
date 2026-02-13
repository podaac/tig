locals {
  name = var.app_name
  environment = var.prefix

  tags = {
    Deployment = var.prefix
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
    null = {
      source  = "hashicorp/null"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}
