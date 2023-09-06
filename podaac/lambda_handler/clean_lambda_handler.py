"""lambda function used for image generation in aws lambda with cumulus"""

import logging
import os
from cumulus_logger import CumulusLogger
from cumulus_process import Process

cumulus_logger = CumulusLogger('tig_lambda_message_cleaner')


class CMACleaner(Process):
    """
    A class to help clean up the CMA message after running tig.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.logger = cumulus_logger

    def process(self):
        """Main process to generate images for granules

        Returns
        ----------
        dict
            Payload that is returned to the cma which is a dictionary with list of granules
        """

        granules = self.input['granules']

        for granule in granules:
            for file in granule['files']:
                if 'description' in file:
                    del file['description']

        return self.input


def handler(event, context):
    """handler that gets called by aws lambda

    Parameters
    ----------
    event: dictionary
        event from a lambda call
    context: dictionary
        context from a lambda call

    Returns
    ----------
        string
            A CMA json message
    """

    #  pylint: disable=duplicate-code
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    logging_level = os.environ.get('LOGGING_LEVEL', 'info')
    cumulus_logger.logger.level = levels.get(logging_level, 'info')
    cumulus_logger.setMetadata(event, context)
    return CMACleaner.cumulus_handler(event, context=context)
