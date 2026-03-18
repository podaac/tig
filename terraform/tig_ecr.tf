data "aws_ecr_authorization_token" "token" {}

locals {
  # 1. Get the very last part of the URI (e.g., "dyen-cumulus-tig:0.13.0@sha256:abcd...")
  uri_parts         = split("/", var.lambda_container_image_uri)
  image_and_version = element(local.uri_parts, length(local.uri_parts) - 1)

  # 2. Extract strictly the repository name by stopping at the first ":" or "@"
  raw_image_name = split("@", split(":", local.image_and_version)[0])[0]

  # 3. Form the valid ECR repository name (No colons or @ symbols!)
  ecr_image_name = "${local.environment}-${local.raw_image_name}"

  # 4. Extract the raw version string by removing the repo name
  raw_version = replace(local.image_and_version, local.raw_image_name, "")

  # 5. Sanitize the version into a perfectly valid ECR tag
  # Turns ":0.13.0@sha256:abcd" into a clean "0.13.0-abcd"
  # Turns "@sha256:abcd" into "abcd"
  ecr_image_tag = trim(replace(replace(local.raw_version, "sha256", ""), "/[:@]+/", "-"), "-")
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
      docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
    EOF
  }
}