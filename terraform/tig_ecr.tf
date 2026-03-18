data "aws_ecr_authorization_token" "token" {}

locals {
  # This regex splits the URI into: [0] registry/path, [1] name, [2] separator (: or @), and [3] tag or sha
  # Example: 123.dkr.ecr.url/my-image@sha256:12345...
  uri_parts = regex("^(.*)/(.*)([:@])(.*)$", var.lambda_container_image_uri)
  
  raw_image_name = local.uri_parts[1]
  separator      = local.uri_parts[2]
  image_version  = local.uri_parts[3]

  ecr_image_name = "${local.environment}-${local.raw_image_name}"
  
  # For ECR, we usually want to push as a tag even if the source was a SHA.
  # If the source was a SHA, we'll strip 'sha256:' to use a clean string as a tag.
  safe_tag = replace(local.image_version, "sha256:", "")
}

resource "aws_ecr_repository" "lambda-image-repo" {
  name = local.ecr_image_name
  tags = var.tags
}

resource "null_resource" "upload_ecr_image" {
  triggers = {
    # It's better to trigger on the URI change rather than every single run
    image_uri = var.lambda_container_image_uri
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-e", "-c"]
    command = <<EOF
      # Docker login
      echo ${data.aws_ecr_authorization_token.token.password} | docker login -u AWS --password-stdin ${data.aws_ecr_authorization_token.token.proxy_endpoint}
      
      # Pull the source (works for both tags and SHAs)
      docker pull --platform=linux/arm64 ${var.lambda_container_image_uri}
      
      # Tag and Push to the new repo
      docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.safe_tag}
      docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.safe_tag}
    EOF
  }
}