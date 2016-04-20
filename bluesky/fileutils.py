"""bluesky.fileutils
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import os
from bluesky.exceptions import BlueSkyConfigurationError

def find_with_datetime(file_or_dir_name, date_time):
    if not file_or_dir_name:
        raise BlueSkyConfigurationError('File not specified')

    # if file does exist with, try filling in datetime codes
    if not os.path.exists(file_or_dir_name):
        file_or_dir_name = date_time.strftime(file_or_dir_name)

        # if it still doesn't exist, raise exception
        if not os.path.isfile(file_or_dir_name):
            raise BlueSkyConfigurationError('File/dir {} does not exist'.format(
                file_or_dir_name))

    return file_or_dir_name

