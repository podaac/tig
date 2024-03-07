"""
==============
regression.py
==============

Test TIG on all our collections.
"""
import filecmp
import os
import shutil
import unittest
from podaac.tig import tig
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import numpy as np
import pytest
import requests
from requests.auth import HTTPBasicAuth
import json


def download_configs(config_dir):

    print("..... downloading configuration files")
    api_url = f"https://api.github.com/repos/podaac/forge-tig-configuration/contents/config-files"
    response = requests.get(api_url)

    if response.status_code == 200:
         for file in response.json():
            url = file.get('download_url')
            config_file = requests.get(url)
            local_filename = file.get('name')
            local_path = os.path.join(config_dir, local_filename)
            with open(local_path, 'wb') as file:
                file.write(config_file.content)

def bearer_token():

    print("..... getting token")

    headers: dict = {'Accept': 'application/json'}
    url: str = f"https://urs.earthdata.nasa.gov/api/users"
    token = None

    # First just try to get a token that already exists
    try:
        resp = requests.get(url + "/tokens", headers=headers,
                                   auth=HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
        response_content = json.loads(resp.content)

        for x in response_content:
            token = x['access_token']

    except Exception as ex:  # noqa E722
        print(ex)
        print("Error getting the token - check user name and password")

    # No tokens exist, try to create one
    if not token:
        try:
            resp = requests.post(url + "/token", headers=headers,
                                        auth=HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
            response_content: dict = json.loads(resp.content)
            token = response_content['access_token']
        except Exception as ex:  # noqa E722
            print(ex)
            print("Error getting the token - check user name and password")

    # If still no token, then we can't do anything
    if not token:
        pytest.skip("Unable to get bearer token from EDL")

    return token


class TestTIG:

    test_dir = os.path.dirname(os.path.realpath(__file__))
    palette_dir = f'{test_dir}/palettes'
    output_dir = f'{test_dir}/output'
    granule_dir = f'{test_dir}/dl_granules'
    config_dir = f'{test_dir}/dl_configs'
    token = bearer_token()

    @pytest.fixture(scope="session")
    def setup_and_teardown(self):

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.granule_dir, exist_ok=True)

        yield

        print('deleting directories')

        #shutil.rmtree(self.output_dir)
        #shutil.rmtree(self.granule_dir)
        #shutil.rmtree(self.config_dir)

    def granule_json(self, collection_short_name):
        '''
        This fixture defines the strategy used for picking a granule from a collection for testing

        Parameters
        ----------
        collection_short_name
        

        Returns
        -------
        umm_json for selected granule
        '''


        collection_cmr_url = f"https://cmr.earthdata.nasa.gov/search/collections.umm_json?short_name={collection_short_name}"
        response_json = requests.get(collection_cmr_url, headers={'Authorization': f'Bearer {self.token}'}).json()
        collection_concept_id = response_json.get('items')[0].get('meta').get('concept-id')

        cmr_url = f"https://cmr.earthdata.nasa.gov/search/granules.umm_json?collection_concept_id={collection_concept_id}&sort_key=-start_date&page_size=1"
        response_json = requests.get(cmr_url, headers={'Authorization': f'Bearer {self.token}'}).json()

        if 'items' in response_json and len(response_json['items']) > 0:
            return response_json['items'][0]
        else:
            pytest.skip(f"No granules found for collection {collection_short_name}. CMR search used was {cmr_url}")


    def download_granule_file(self, granule_json, collection_short_name):

        related_urls = granule_json.get('umm').get('RelatedUrls')

        def download_file(url):

            local_filename = os.path.join(self.granule_dir, f"{collection_short_name}.nc")
            response = requests.get(url, headers={'Authorization': f'Bearer {self.token}'}, stream=True)
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return local_filename

        granule_url = None
        for x in related_urls:
            if x.get('Type') == "GET DATA" and x.get('Subtype') in [None, 'DIRECT DOWNLOAD'] and '.bin' not in x.get('URL'):
                granule_url = x.get('URL')

        if granule_url:
            return download_file(granule_url)
        else:
            pytest.skip(f"Unable to find download URL for {granule_json['meta']['concept-id']}")


    def download_granule(self, collection_short_name):

        granule_json = self.granule_json(collection_short_name)
        return self.download_granule_file(granule_json,collection_short_name)

    @staticmethod
    def generate_test_values():

        config_dir = os.path.dirname(os.path.realpath(__file__)) + "/dl_configs"
        os.makedirs(config_dir, exist_ok=True)

        download_configs(config_dir)
        files = os.listdir(config_dir)
        return [file.strip('.cfg') for file in files]


    @pytest.mark.usefixtures("setup_and_teardown")
    @pytest.mark.parametrize("collection_short_name", generate_test_values())
    def test_image_generation(self, collection_short_name):
        
        print(f"generate_images for ... {collection_short_name}")
        input_file = self.download_granule(collection_short_name)
        config_file = os.path.join(self.config_dir, collection_short_name + '.cfg')
        output_dir = os.path.join(self.output_dir, collection_short_name)
        os.makedirs(output_dir, exist_ok=True)

        # Your test logic here
        image_gen = tig.TIG(input_file, output_dir, config_file, self.palette_dir)
        image_gen.generate_images()

if __name__ == "__main__":
    pytest.main()
