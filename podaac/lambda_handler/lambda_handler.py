"""lambda function used for image generation in aws lambda with cumulus"""

import json
import logging
import os
import re
from shutil import rmtree
import multiprocessing as mp
import traceback
import requests

import botocore
from cumulus_logger import CumulusLogger
from cumulus_process import Process, s3
from podaac.tig import tig
from podaac.lambda_handler.cumulus_cli_handler.handlers import activity

cumulus_logger = CumulusLogger('image_generator')


def clean_tmp(remove_matlibplot=True):
    """ Deletes everything in /tmp """
    temp_folder = '/tmp'
    temp_files = os.listdir(temp_folder)

    cumulus_logger.info("Removing everything in tmp folder {}".format(temp_files))
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                if filename.startswith('matplotlib'):
                    if remove_matlibplot:
                        rmtree(file_path)
                else:
                    rmtree(file_path)
        except OSError as ex:
            cumulus_logger.error('Failed to delete %s. Reason: %s' % (file_path, ex))

    temp_files = os.listdir(temp_folder)
    cumulus_logger.info("After Removing everything in tmp folder {}".format(temp_files))


def generate_images(local_file, path, config_file, palette_dir, granule_id, variables, logger, conn):
    """Function to call in multiprocess to generate images"""
    try:
        image_gen = tig.TIG(local_file, path, config_file, palette_dir, variables=variables, logger=logger)
        images = image_gen.generate_images(granule_id=granule_id)
        conn.send(({'status': 'success', 'data': images}, None))
    except Exception as e:
        error_traceback = traceback.format_exc()
        conn.send(({'status': 'error', 'data': None}, (str(e), error_traceback)))
    finally:
        conn.close()


class ImageGenerator(Process):
    """
    Image generation class to generate image for a granule file and upload to s3


    Attributes
    ----------
    processing_regex : str
        regex for nc file to generate image
    logger: logger
        cumulus logger
    config: dictionary
        configuration from cumulus


    Methods
    -------
    upload_file_to_s3('/user/test/test.png', 's3://bucket/path/test.png')
        uploads a local file to s3
    get_file_type(test.png, [....])
        gets the file type for a png
    get_bucket(test.png, [....], {....})
        gets the bucket where png to be stored
    process()
        main function ran for image generation
    generate_file_dictionary({file_data}, /user/test/test.png, test.png, [....], {....})
        creates the dictionary data for a generated image
    image_generate({file_data}, "/tmp/configuration.cfg", "/tmp/palette_dir", "granule.nc" )
        generates all images for a nc file
    get_config()
        downloads configuration file for tig
    download_file_from_s3('s3://my-internal-bucket/dataset-config/MODIS_A.2019.cfg', '/tmp/workspace')
        downloads a file from s3 to a directory
    """

    def __init__(self, *args, **kwargs):

        self.processing_regex = '(.*\\.nc$)'
        super().__init__(*args, **kwargs)
        self.logger = cumulus_logger

    def clean_all(self):
        """ Removes anything saved to self.path """
        rmtree(self.path)
        clean_tmp()

    def download_file_from_s3(self, s3file, working_dir):
        """ Download s3 file to local

        Parameters
        ----------
        s3file: str
            path location of the file  Ex. s3://my-internal-bucket/dataset-config/MODIS_A.2019.cfg
        working_dir: str
            local directory path where the s3 file should be downloaded to

        Returns
        ----------
        str
            full path of the downloaded file
        """
        try:
            return s3.download(s3file, working_dir)
        except botocore.exceptions.ClientError as ex:
            self.logger.error("Error downloading file %s: %s" % (s3file, working_dir), exc_info=True)
            raise ex

    def upload_file_to_s3(self, filename, uri):
        """ Upload a local file to s3 if collection payload provided

        Parameters
        ----------
        filename: str
            path location of the file
        uri: str
            s3 string of file location
        """
        try:
            return s3.upload(filename, uri, extra={"ACL": "bucket-owner-full-control"})
        except botocore.exceptions.ClientError as ex:
            self.logger.error("Error uploading file %s: %s" % (os.path.basename(os.path.basename(filename)), str(ex)), exc_info=True)
            raise ex

    @staticmethod
    def get_file_type(filename, files):
        """Get custom file type, default to metadata

        Parameters
        ----------
        filename: str
            filename of a file
        files: str
            collection list of files with attributes of specific file type
        """

        for collection_file in files:
            if re.match(collection_file.get('regex', '*.'), filename):
                return collection_file['type']
        return 'metadata'

    @staticmethod
    def get_bucket(filename, files, buckets):
        """Extract the bucket from the files

        Parameters
        ----------
        filename: str
            filename of a file
        files: list
            collection list of files with attributes of specific file type
        buckets: list
            list of buckets

        Returns
        ----------
        str
            string of the bucket the file to be stored in
        """
        bucket_type = "public"
        for file in files:
            if re.match(file.get('regex', '*.'), filename):
                bucket_type = file['bucket']
                break
        return buckets[bucket_type]

    @classmethod
    def cumulus_activity(cls, arn=os.getenv('ACTIVITY_ARN')):
        """ Run an activity using Cumulus messaging (cumulus-message-adapter) """
        activity(cls.cumulus_handler, arn)

    def download_palette_files(self, config):
        """Get palette files for image generations

        Parameters
        ----------
        config: str
            path location of configuration file
        """
        # url = "https://hitide.podaac.sit.earthdatacloud.nasa.gov/palettes"
        palette_base_url = os.environ.get("PALETTE_URL")
        with open(config) as json_file:
            data = json.load(json_file)
            palettes = []
            for variable in data['imgVariables']:
                palette = variable.get('palette')
                if palette not in palettes:
                    palettes.append(palette)
                    palette_url = "{}/{}.json".format(palette_base_url, palette)
                    response = requests.get(palette_url, timeout=60)
                    palette_full_path = "{}/{}.json".format(self.path, palette)
                    with open(palette_full_path, 'wb') as file_:
                        file_.write(response.content)

    def get_config(self):
        """Get configuration file for image generations
        Returns
        ----------
        str
            string of the filepath to the configuration
        """
        config_url = os.environ.get("CONFIG_URL")
        config_name = self.config['collection']['name']
        config_bucket = os.environ.get('CONFIG_BUCKET')
        config_dir = os.environ.get("CONFIG_DIR")

        if config_url:
            file_url = "{}/{}.cfg".format(config_url, config_name)
            response = requests.get(file_url, timeout=60)
            cfg_file_full_path = "{}/{}.cfg".format(self.path, config_name)
            with open(cfg_file_full_path, 'wb') as file_:
                file_.write(response.content)

        elif config_bucket and config_dir:
            config_s3 = 's3://{}.cfg'.format(os.path.join(config_bucket, config_dir, config_name))
            cfg_file_full_path = self.download_file_from_s3(config_s3, self.path)
        else:
            raise ValueError('Environment variable to get configuration files were not set')

        return cfg_file_full_path

    def process(self):
        """Main process to generate images for granules

        Returns
        ----------
        dict
            Payload that is returned to the cma which is a dictionary with list of granules
        """

        config_file_path = self.get_config()

        granules = self.input['granules']
        append_output = {}

        if self.kwargs.get('context', None):
            try:
                aws_request_id = self.kwargs.get('context').aws_request_id
                collection_name = self.config.get('collection').get('name')
                message = json.dumps({
                    "aws_request_id": aws_request_id,
                    "collection": collection_name
                })
                self.logger.info(message)
            except AttributeError:
                pass

        self.download_palette_files(config_file_path)

        for granule in granules:
            granule_id = granule['granuleId']
            for file_ in granule['files']:
                uploaded_images = self.image_generate(file_, config_file_path, self.path, granule_id)
                if uploaded_images:
                    append_output[granule_id] = append_output.get(granule_id, []) + uploaded_images
            if granule_id in append_output:
                granule['files'] += append_output[granule_id]

        return self.input

    def generate_file_dictionary(self, file_, image_file, output_file_basename, collection_files, buckets, variable, group):
        """function to generate an information for an image for cumulus

        Parameters
        ----------
        file_: list
            dictionary contain data about a granule file
        image_file: str
            path location of the generated image file
        output_file_basename: str
            the file name of the generated file
        collection_files: list
            collection list of files on how to handle each file type
        buckets: dict
            dictionary of buckets
        variable: string
            variable used to generate image file
        group: string
            group the variable belong to could be none

        Returns
        ----------
        dict
            dictionary data of an image uploaded to s3
        """

        description = variable
        if group is not None:
            description = f'{group}/{variable}'

        try:
            prefix = os.path.dirname(file_['key'])
            upload_file_dict = {
                "key": f'{prefix}/{output_file_basename}',
                "fileName": output_file_basename,
                "bucket": self.get_bucket(output_file_basename, collection_files, buckets)['name'],
                "size": os.path.getsize(image_file),
                "type": self.get_file_type(output_file_basename, collection_files),
                "description": description
            }
            s3_link = f's3://{upload_file_dict["bucket"]}/{upload_file_dict["key"]}'

            self.upload_file_to_s3(image_file, s3_link)
            return upload_file_dict

        except FileNotFoundError as ex:
            self.logger.error("Error generating image data FileNotFoundError: {}".format(ex), exc_info=True)
            raise ex
        except KeyError as ex:
            self.logger.error("Error generating image data KeyError: {}".format(ex), exc_info=True)
            raise ex

    def image_generate(self, file_, config_file, palette_dir, granule_id):
        """
        Main function to handle image generation workflow.

        Parameters
        ----------
        file_: dict
            Dictionary containing data about a granule file.
        config_file: str
            File path of configuration file that was downloaded from S3.
        palette_dir: str
            Directory of all the palettes for image generation.
        granule_id: str
            Granule ID of the granule the images are generated for.

        Returns
        -------
        list
            List of dictionaries with information about images uploaded to S3.
        """
        if not self._is_valid_input(file_):
            return None

        try:
            local_file = self._download_file(file_)
            variables_config = self._load_config(config_file)
            image_list = self._generate_images(local_file, config_file, palette_dir, granule_id, variables_config)
            uploaded_files = self._upload_images(file_, image_list)
            return uploaded_files

        except Exception as ex:
            self.logger.error("Error during image generation: {}".format(ex), exc_info=True)
            raise

    def _is_valid_input(self, file_):
        """Check if the input file is valid for processing."""
        input_file = f's3://{file_["bucket"]}/{file_["key"]}'
        data_type = file_['type']
        return re.match(self.processing_regex, input_file) or data_type == "data"

    def _download_file(self, file_):
        """Download the input file from S3."""
        input_file = f's3://{file_["bucket"]}/{file_["key"]}'
        try:
            return s3.download(input_file, path=self.path)
        except botocore.exceptions.ClientError as ex:
            self.logger.error("Error downloading file from S3: {}".format(ex), exc_info=True)
            raise

    def _load_config(self, config_file):
        """Load the configuration file."""
        try:
            with open(config_file) as config_f:
                return json.load(config_f).get('imgVariables', [])
        except Exception as ex:
            self.logger.error("Error loading configuration file: {}".format(ex), exc_info=True)
            raise

    def _generate_images(self, local_file, config_file, palette_dir, granule_id, variables_config):
        """Generate images using multiprocessing."""
        parent_connections, processes = [], []
        var_list = [variables_config]

        for variables in var_list:
            if variables:
                parent_conn, child_conn = mp.Pipe()
                parent_connections.append(parent_conn)
                process = mp.Process(
                    target=generate_images,
                    args=(local_file, self.path, config_file, palette_dir, granule_id, variables, self.logger, child_conn)
                )
                processes.append(process)

        for process in processes:
            process.start()

        image_list, errors = self._collect_process_results(parent_connections)

        for process in processes:
            process.join()

        if errors:
            raise Exception("\n".join(errors))

        return image_list

    def _collect_process_results(self, parent_connections):
        """Collect results from all child processes."""
        image_list, errors = [], []

        for parent_connection in parent_connections:
            result, error = parent_connection.recv()
            if error:
                error_msg, traceback_str = error
                errors.append(f"Process error: {error_msg}\n{traceback_str}")
            elif result['status'] == 'success':
                image_list.extend(result['data'])

        for conn in parent_connections:
            conn.close()

        return image_list, errors

    def _upload_images(self, file_, image_list):
        """Upload generated images to S3."""
        uploaded_files = []
        collection_files = self.config.get('collection', {}).get('files', [])
        buckets = self.config.get('buckets')

        for image_dict in image_list:
            try:
                image_file = image_dict.get('image_file')
                variable = image_dict.get('variable')
                group = image_dict.get('group')
                output_file_basename = os.path.basename(image_file)

                upload_file_dict = self.generate_file_dictionary(
                    file_, image_file, output_file_basename, collection_files, buckets, variable, group
                )
                uploaded_files.append(upload_file_dict)
            except Exception as ex:
                self.logger.error("Error uploading image to S3: {}".format(ex), exc_info=True)
                raise

        return uploaded_files

    @classmethod
    def handler(cls, event, context=None, path=None, noclean=False):
        """ General event handler """
        return cls.run(path=path, noclean=noclean, context=context, **event)

    @classmethod
    def run(cls, *args, **kwargs):
        """ Run this payload with the given Process class """
        noclean = kwargs.pop('noclean', False)
        process = cls(*args, **kwargs)
        try:
            output = process.process()
        finally:
            if not noclean:
                process.clean_all()
        return output


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
    clean_tmp(remove_matlibplot=False)
    return ImageGenerator.cumulus_handler(event, context=context)


if __name__ == "__main__":
    ImageGenerator.cli()
