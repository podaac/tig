"""Handler module for ecs activity"""

import os
import json
import signal
import sys
import traceback
from functools import partial
import boto3
from botocore.client import Config
from botocore.vendored.requests.exceptions import ReadTimeout
from cumulus_logger import CumulusLogger

logger = CumulusLogger('image_generator_activity')

"""
cls is the Process subclass for a specific data source, such as MODIS, ASTER, etc.
"""

SFN_PAYLOAD_LIMIT = 32768
TASK_TOKEN = None


def shutdown(sfn, signum, frame):  # pylint: disable=W0613
    """Shutdown function when getting termination signal for ecs"""
    logger.info("Caught SIGTERM, shutting down")
    if TASK_TOKEN:
        ecs_error = "Caught SIGTERM, ECS is terminating container"
        sfn.send_task_failure(taskToken=TASK_TOKEN, error=ecs_error)
    logger.info("ECS service have been terminated last token: {}".format(TASK_TOKEN))
    # Finish any outstanding requests, then...
    sys.exit(0)


def activity(handler, arn=os.getenv('ACTIVITY_ARN')):
    """ An activity service for use with AWS Step Functions """
    sfn = boto3.client('stepfunctions', config=Config(read_timeout=70))
    signal.signal(signal.SIGTERM, partial(shutdown, sfn))
    while True:
        get_and_run_task(handler, sfn, arn)


def get_and_run_task(handler, sfn, arn):
    """ Get and run a single task as part of an activity """
    global TASK_TOKEN  # pylint: disable=W0603
    logger.info("query for task")
    try:
        task = sfn.get_activity_task(activityArn=arn, workerName=__name__)
    except ReadTimeout:
        logger.warning("Activity read timed out. Trying again.")
        return

    token = task.get('taskToken', None)
    if not token:
        logger.info("No activity task")
        return
    TASK_TOKEN = token

    try:
        payload = json.loads(task['input'])
        output = json.dumps(handler(event=payload))
        sfn.send_task_success(taskToken=task['taskToken'], output=output)
        TASK_TOKEN = None
    except MemoryError as ex:
        err = str(ex)
        logger.error("Memory error when running task: {}".format(err))
        trace_back = traceback.format_exc()
        err = (err[252] + ' ...') if len(err) > 252 else err
        sfn.send_task_failure(taskToken=task['taskToken'], error=str(err), cause=trace_back)
        raise ex
    except Exception as ex:  # pylint: disable=W0703
        err = str(ex)
        logger.error("Exception when running task: {}".format(err))
        trace_back = traceback.format_exc()
        err = (err[252] + ' ...') if len(err) > 252 else err
        sfn.send_task_failure(taskToken=task['taskToken'], error=str(err), cause=trace_back)
        TASK_TOKEN = None
