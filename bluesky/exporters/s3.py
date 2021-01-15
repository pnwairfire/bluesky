"""bluesky.exporters.s3"""

__author__ = "Joel Dubowy"

import copy
import logging
import os
import shutil
import tempfile
import traceback

import boto3

from bluesky import io
from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'S3Exporter'
]

__version__ = "0.1.0"


class S3Exporter(ExporterBase):

    EXPORT_KEY = 's3'

    def __init__(self, extra_exports):
        super(S3Exporter, self).__init__(extra_exports)
        if not self.config('bucket'):
            raise BlueSkyConfigurationError("Specify at least ")

        self._s3_client = boto3.client('s3')

    ##
    ## Public Interface
    ##

    def export(self, fires_manager):
        key_prefix = self._get_key_prefix(fires_manager)
        fires_manager.export = fires_manager.export or {}
        fires_manager.export['s3'] = {
            "bucket": self.config('bucket'),
            "tarball": self._upload_tarball(fires_manager, key_prefix),
            "output": self._upload_output(fires_manager, key_prefix)
        }

    def _get_key_prefix(self, fires_manager):
        key_prefix = self.config('key_prefix')
        if key_prefix:
            return os.path.join(key_prefix, fires_manager.run_id)
        else:
            return fires_manager.run_id

    def _upload_output(self, fires_manager, key_prefix):
        try:
            key = os.path.join(key_prefix, self.config('json_output_filename'))
            content = self._get_output_dump(fires_manager)
            self._s3_client.put_object(Body=content,
                Bucket=self.config('bucket'), Key=key)
            return {
                "key": key,
                "url": self._get_s3_url(key)
            }

        except Exception as e:
            logging.warning("Failed to upload output JSON data to AWS S3")
            logging.debug(traceback.format_exc())

    def _upload_tarball(self, fires_manager, key_prefix):
        if not self.config('include_tarball'):
            logging.debug("Skipping upload of tarball to S3")
            return

        temp_dir = tempfile.mkdtemp()
        try:
            tarball_file_name = self._bundle(fires_manager, temp_dir,
                create_tarball=True)
            key = os.path.join(key_prefix, os.path.basename(tarball_file_name))
            self._s3_client.upload_file(tarball_file_name,
                self.config('bucket'), key)
            return {
                "key": key,
                "url": self._get_s3_url(key)
            }

        except Exception as e:
            logging.warning("Failed to upload output tarball to AWS S3")
            logging.debug(traceback.format_exc())

        finally:
            shutil.rmtree(temp_dir)

    def _get_s3_url(self, key):
        try:
            region = self._s3_client._client_config.region_name
        except:
            region = self.config("default_region_name")

        return "https://{bucket}.s3-{region}.amazonaws.com/{key}".format(
            bucket=self.config('bucket'), region=region,
            key=key.lstrip('/'))
