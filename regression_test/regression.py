"""
==============
regression.py
==============

Test Tig on all our collections.
"""

import json
import os
import shutil
import unittest

import pytest
import requests
from requests.auth import HTTPBasicAuth
from podaac.tig import tig

def download_configs(config_dir):
    print("..... downloading configuration files")
    api_url = "https://api.github.com/repos/podaac/forge-tig-configuration/contents/config-files"
    response = requests.get(api_url)

    if response.status_code == 200:
        for file in response.json():
            url = file.get('download_url')
            local_filename = file.get('name')
            subdir_name, _ = os.path.splitext(local_filename)
            subdir_path = os.path.join(config_dir, subdir_name)
            local_path = os.path.join(subdir_path, local_filename)

            if not os.path.exists(local_path):
                config_file = requests.get(url)
                try:
                    content_json = config_file.json()
                except Exception:
                    continue

                if "imgVariables" in content_json:
                    os.makedirs(subdir_path, exist_ok=True)
                    with open(local_path, 'w') as f:
                        json.dump(content_json, f, indent=2)
                    print(f"Downloaded: {local_path}")

def download_palettes(config_dir):
    print("..... downloading palettes")
    api_url = "https://api.github.com/repos/podaac/forge-tig-configuration/contents/palettes"
    response = requests.get(api_url)

    if response.status_code == 200:
        os.makedirs(config_dir, exist_ok=True)
        for file in response.json():
            url = file.get('download_url')
            local_filename = file.get('name')
            local_path = os.path.join(config_dir, local_filename)

            if not os.path.exists(local_path):
                file_response = requests.get(url)
                with open(local_path, 'wb') as f:
                    f.write(file_response.content)
                print(f"Downloaded: {local_path}")

def bearer_token():
    print("..... getting token")

    # Check for required environment variables
    if 'CMR_USER' not in os.environ or 'CMR_PASS' not in os.environ:
        raise EnvironmentError("Environment variables 'CMR_USER' and/or 'CMR_PASS' must be set.")

    headers: dict = {'Accept': 'application/json'}
    url: str = "https://urs.earthdata.nasa.gov/api/users"
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
    palette_dir = f'{test_dir}/regression_output/palettes'
    config_dir = f'{test_dir}/regression_output'
    token = bearer_token()

    @pytest.fixture(scope="session")
    def setup_and_teardown(self):

        os.makedirs(self.config_dir, exist_ok=True)

        yield

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


    def download_granule_file(self, granule_json, collection_short_name, config_dir):
        """
        Downloads the granule file for the specified collection into the config directory,
        within a subdirectory named after the collection, only if it doesn't already exist.
        Also creates a meta-data.txt file containing the related URL.
        """

        related_urls = granule_json.get('umm').get('RelatedUrls')
        collection_dir = os.path.join(config_dir, collection_short_name)
        local_filename = os.path.join(collection_dir, f"{collection_short_name}.nc")
        meta_filename = os.path.join(collection_dir, "meta-data.txt")

        # Check if the granule file already exists
        if os.path.exists(local_filename):
            return local_filename  # Already present, do nothing

        # Find granule URL
        granule_url = None
        for x in related_urls:
            if x.get('Type') == "GET DATA" and x.get('Subtype') in [None, 'DIRECT DOWNLOAD'] and '.bin' not in x.get('URL'):
                granule_url = x.get('URL')
                break

        if granule_url:
            os.makedirs(collection_dir, exist_ok=True)
            response = requests.get(granule_url, headers={'Authorization': f'Bearer {self.token}'}, stream=True)
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            # Write the related URL to mete-data.txt
            with open(meta_filename, 'w') as meta_f:
                meta_f.write(granule_url + '\n')
            print(f"Downloaded: {local_filename}")
            return local_filename
        else:
            pytest.skip(f"Unable to find download URL for {granule_json['meta']['concept-id']}")
            return None

    def download_granule(self, collection_short_name):

        granule_json = self.granule_json(collection_short_name)
        return self.download_granule_file(granule_json, collection_short_name, self.config_dir)

    @staticmethod
    def generate_test_values():

        config_dir = os.path.dirname(os.path.realpath(__file__)) + "/regression_output"
        palette_dir = os.path.dirname(os.path.realpath(__file__)) + "/regression_output/palettes"
        os.makedirs(config_dir, exist_ok=True)

        download_configs(config_dir)
        download_palettes(palette_dir)
        files = [
            f for f in os.listdir(config_dir)
            if f != 'palettes'
        ]        
        return files


    @pytest.mark.usefixtures("setup_and_teardown")
    @pytest.mark.parametrize("collection_short_name", generate_test_values())
    def test_footprint_generation(self, collection_short_name):
        
        print(f"generate footprint for ... {collection_short_name}")

        config_dir = self.config_dir
        input_file = self.download_granule(collection_short_name)
        config_file = os.path.join(config_dir, collection_short_name, f"{collection_short_name}.cfg")

        if input_file:
            output_dir = os.path.join(config_dir, collection_short_name, 'output_images')
            os.makedirs(output_dir, exist_ok=True)

            # Your test logic here
            image_gen = tig.TIG(input_file, output_dir, config_file, self.palette_dir)
            image_gen.generate_images()


if __name__ == "__main__":
    pytest.main()