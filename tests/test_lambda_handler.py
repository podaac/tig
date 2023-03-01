"""Test cases for tig lambda_handler"""

import json
import os
import boto3
import pytest
from jsonschema import validate

from podaac.lambda_handler import lambda_handler
from moto import mock_s3
from mock import patch, Mock

file_schema = {
  "type": "array",
  "items": {
    "additionalProperties": False,
    "type": "object",
    "required": [
      "bucket",
      "key"
    ],
    "properties": {
      "bucket": {
        "description": "Bucket where file is archived in S3",
        "type": "string"
      },
      "checksum": {
        "description": "Checksum value for file",
        "type": "string"
      },
      "checksumType": {
        "description": "Type of checksum (e.g. md5, sha256, etc)",
        "type": "string"
      },
      "fileName": {
        "description": "Name of file (e.g. file.txt)",
        "type": "string"
      },
      "key": {
        "description": "S3 Key for archived file",
        "type": "string"
      },
      "size": {
        "description": "Size of file (in bytes)",
        "type": "number"
      },
      "source": {
        "description": "Source URI of the file from origin system (e.g. S3, FTP, HTTP)",
        "type": "string"
      },
      "type": {
        "description": "Type of file (e.g. data, metadata, browse)",
        "type": "string"
      }
    }
  }
}

def test_get_bucket():
    """Test get_bucket function to get the correct bucket for a file"""

    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = dir_path + '/input.txt'

    with open(input_file) as json_event:
        event = json.load(json_event)
    files = event['meta']['collection']['files']
    buckets = event['meta']['buckets']
    bucket = lambda_handler.ImageGenerator.get_bucket('test.png', files, buckets)
    assert bucket['name'] == 'test-prefix-protected-test'


def test_get_file_type():
    """Test get_file_type function gets the correct type for a file"""

    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = dir_path + '/input.txt'

    with open(input_file) as json_event:
        event = json.load(json_event)
    files = event['meta']['collection']['files']
    file_type = lambda_handler.ImageGenerator.get_file_type('test.png', files)
    assert file_type == 'data'


@mock_s3
def test_lambda_handler_upload():
    """Test lambda handler function upload_file_to_s3 uploads files to s3"""

    bucket = "test-prefix-protected-test"
    aws_s3 = boto3.resource('s3', region_name='us-east-1')
    aws_s3.create_bucket(Bucket=bucket)

    image_generator = lambda_handler.ImageGenerator(input={})
    #files = image_generator.fake_image_generator()

    test_dir = os.path.dirname(os.path.realpath(__file__))
    input_dir = f'{test_dir}/input'
    nc_file = f'{input_dir}/cyg.ddmi.s20201031-000000-e20201031-235959.l2.surface-flux-cdr.a10.d10.nc'

    image_generator.upload_file_to_s3(nc_file, 's3://{}/{}'.format(bucket, os.path.basename(nc_file)))
    image_generator.clean_all()

    aws_s3.Object(bucket, os.path.basename(nc_file)).load()


@mock_s3
def test_get_config():
    """Test lambda handler function upload_file_to_s3 uploads files to s3"""
    aws_s3 = boto3.resource('s3', region_name='us-east-1')

    test_dir = os.path.dirname(os.path.realpath(__file__))
    config_dir = f'{test_dir}/configs'
    cfg_file = f'{config_dir}/PODAAC-CYGNS-C2H10.cfg'
    s3_client = boto3.client('s3', region_name='us-east-1')

    os.environ["CONFIG_BUCKET"] = "internal-bucket"
    os.environ["CONFIG_DIR"] = "dataset-config"
    aws_s3.create_bucket(Bucket='internal-bucket')

    with open(cfg_file, 'rb') as data:
        s3_client.put_object(Bucket='internal-bucket',
                         Key='dataset-config/JASON-1_L2_OST_GPN_E.cfg',
                         Body=data)

    image_generator = lambda_handler.ImageGenerator(input={})
    image_generator.config = {
        'collection': {
            'name' : 'JASON-1_L2_OST_GPN_E'
        }
    }
    path = image_generator.get_config()    
    assert os.path.isfile(path)
    image_generator.clean_all()


@patch('requests.get')
def test_get_config_url(mocked_get):
    """Test lambda handler function upload_file_to_s3 uploads files to s3"""
    mocked_get.return_value = Mock(status_code=201, content=b'hello world')
    os.environ["CONFIG_URL"] = "https://hitide.podaac.sit.earthdatacloud.nasa.gov/dataset-configs"
    image_generator = lambda_handler.ImageGenerator(input={})
    image_generator.config = {
        'collection': {
            'name' : 'MODIS_A-JPL-L2P-v2014.0'
        }
    }
    path = image_generator.get_config()    
    assert os.path.isfile(path)
    assert os.path.basename(path) == 'MODIS_A-JPL-L2P-v2014.0.cfg'

    with open(path, 'r') as f:
        content = f.read()
        assert 'hello world' == content

    image_generator.clean_all()


def test_get_config_no_setting():
    """Test lambda handler function upload_file_to_s3 uploads files to s3"""

    os.environ["CONFIG_BUCKET"] = ""
    os.environ["CONFIG_DIR"] = ""
    os.environ["CONFIG_URL"] = ""
    image_generator = lambda_handler.ImageGenerator(input={})
    image_generator.config = {
        'collection': {
            'name' : 'MODIS_A-JPL-L2P-v2014.0'
        }
    }
    try:
        path = image_generator.get_config()    
        assert False
    except Exception:
        # exception expected
        pass


@mock_s3
@patch('requests.get')
def test_lambda_handler_cumulus(mocked_get):
    """Test lambda handler to run through cumulus handler"""

    test_dir = os.path.dirname(os.path.realpath(__file__))

    palette_file = f'{test_dir}/palettes/paletteMedspirationIndexed.json'

    with open(palette_file) as palette_json_file:
        palette_data = json.load(palette_json_file)
        mocked_get.return_value = Mock(status_code=200, content=json.dumps(palette_data).encode('utf-8'))

    bucket = "test-prefix-protected-test"
    aws_s3 = boto3.resource('s3', region_name='us-east-1')
    aws_s3.create_bucket(Bucket=bucket)

    input_dir = f'{test_dir}/input'
    config_dir = f'{test_dir}/configs'
    nc_file = f'{input_dir}/cyg.ddmi.s20201031-000000-e20201031-235959.l2.surface-flux-cdr.a10.d10.nc'
    cfg_file = f'{config_dir}/PODAAC-CYGNS-C2H10.cfg'

    with open(nc_file, 'rb') as data:
        aws_s3.Bucket(bucket).put_object(Key='test_folder/test_granule.nc', Body=data)

    s3_client = boto3.client('s3', region_name='us-east-1')    

    # Mock S3 download here:
    os.environ["CONFIG_BUCKET"] = "internal-bucket"
    os.environ["CONFIG_DIR"] = "dataset-config"
    os.environ["CONFIG_URL"] = ""
    aws_s3.create_bucket(Bucket='internal-bucket')

    with open(cfg_file, 'rb') as data:
        s3_client.put_object(Bucket='internal-bucket',
                         Key='dataset-config/JASON-1_L2_OST_GPN_E.cfg',
                         Body=data)

    s3_client.get_object(Bucket="internal-bucket",
                         Key='dataset-config/JASON-1_L2_OST_GPN_E.cfg',
                         )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = dir_path + '/input.txt'

    with open(input_file) as json_event:
        event = json.load(json_event)
        granules = event.get('payload').get('granules')
        for granule in granules:
            files = granule.get('files')
            is_valid_shema = validate(instance=files, schema=file_schema)
            assert is_valid_shema is None

    output = lambda_handler.handler(event, {})

    for granule in output.get('payload').get('granules'):
        is_valid_shema = validate(instance=granule.get('files'), schema=file_schema)
        assert is_valid_shema is None  
        for file in granule.get('files'):

            if file.get('fileName').endswith('.png'):
                bucket = file.get('bucket')
                key = file.get('key')
                # test if file in s3 if not then test fails
                aws_s3.Object(bucket, key).load()
