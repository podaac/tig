data "aws_ecr_authorization_token" "token" {}

locals {
  lambda_container_image_uri_split = split("/", var.lambda_container_image_uri)
  ecr_image_name_and_tag           = split(":", element(local.lambda_container_image_uri_split, length(local.lambda_container_image_uri_split) - 1))
  ecr_image_name                   = "${local.environment}-${element(local.ecr_image_name_and_tag, 0)}"
  ecr_image_tag                    = element(local.ecr_image_name_and_tag, 1)
}

resource aws_ecr_repository "lambda-image-repo" {
  name = local.ecr_image_name
  tags = var.tags
}

resource "null_resource" "upload_ecr_image" {

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-e", "-c"]
    command = <<EOF
      # Docker login
      echo ${data.aws_ecr_authorization_token.token.password} | docker login -u AWS --password-stdin ${data.aws_ecr_authorization_token.token.proxy_endpoint}
      # Docker image upload
      docker pull --platform=linux/arm/v7 ${var.lambda_container_image_uri}
      docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
    EOF
  }
}