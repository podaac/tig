resource "aws_sfn_state_machine" "imagetest" {
  name     = "${var.prefix}-tig"
  role_arn = aws_iam_role.step.arn

  definition = <<EOF
{
  "Comment": "Image Processing",
  "StartAt": "ImageProcess",
  "States": {
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
          "MaxAttempts": 1
        }
      ],
      "Next": "WorkflowSucceeded"
    },
    "WorkflowSucceeded": {
      "Type": "Succeed"
    },
    "WorkflowFailed": {
      "Type": "Fail",
      "Cause": "Workflow failed"
    }
  }
}
EOF
}