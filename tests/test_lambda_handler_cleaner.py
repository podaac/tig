import json
import os
from podaac.lambda_handler import clean_lambda_handler

def test_get_bucket():
    """Test get_bucket function to get the correct bucket for a file"""

    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = dir_path + '/input.txt'

    with open(input_file) as json_event:
        event = json.load(json_event)
    output = clean_lambda_handler.handler(event, {})

    for file in output['payload']['granules'][0]['files']:
        assert 'description' not in file