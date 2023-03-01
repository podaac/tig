# Overview

Terraform scripts to create aws lambda for tig in cumulus.

# Deploy in Cumulus

## TIG module
 ```code
module "tig" {
  source = "https://cae-artifactory.jpl.nasa.gov/artifactory/general-develop/gov/nasa/podaac/cumulus/tig-terraform/tig-terraform-0.1.0-alpha.2+8a8b45b.zip"
  // Lambda variables
  prefix = var.prefix
  image = var.tig_image
  role = module.cumulus.lambda_processing_role_arn
  cmr_environment = var.cmr_environment
  subnet_ids = var.subnet_ids
  security_group_ids = [aws_security_group.no_ingress_all_egress.id]
  task_logs_retention_in_days = var.task_logs_retention_in_days
  config_bucket = "${var.prefix}-internal"
  config_dir = var.tig_config_dir
  memory_size = var.tig_memory_size
}

```

## TIG in workflow

```code
"ImageProcess": {
        "Parameters": {
          "cma": {
            "event.$": "$",
            "task_config": {
              "collection": "{$.meta.collection}",
              "buckets": "{$.meta.buckets}",
              "cumulus_message": {
                "input": "{$.payload}"
              }
            }
          }
        },
        "Type": "Task",
        "Resource": "${module.tig.tig_task_lambda_arn}",
        "Catch": [
          {
            "ErrorEquals": [
              "States.ALL"
            ],
            "ResultPath": "$.exception",
            "Next": "WorkflowFailed"
          }
        ],
        "Retry": [
          {
            "ErrorEquals": [
              "States.ALL"
            ],
            "IntervalSeconds": 2,
            "MaxAttempts": 3
          }
        ],
        "Next": <next step>
      }
```