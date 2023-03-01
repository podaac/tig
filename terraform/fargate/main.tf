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
      version = ">= 2.31.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 2.1"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}
