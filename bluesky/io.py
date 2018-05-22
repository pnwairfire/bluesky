"""bluesky.io"""

__author__ = "Joel Dubowy"

import logging
import os
import shutil

from pyairfire.io import *

from bluesky.exceptions import BlueSkyConfigurationError

def create_dir_or_handle_existing(dir_to_create, handle_existing):
    """Creates the specified dir if it doesn't exist, or deals with
    it's existence in one of three ways:

     'fail': raises exception
     'replace': deletes existing directory and continues
     'write_in_place': continues without any action
    """
    dir_to_create = os.path.abspath(dir_to_create)

    if os.path.exists(dir_to_create):
        logging.debug("Output dir exists; handling with '%s'", handle_existing)
        if handle_existing == 'fail':
            raise RuntimeError("{} already exists".format(dir_to_create))
        elif handle_existing == 'write_in_place':
            # TODO: make this work recursively. see
            #    https://docs.python.org/3.5/distutils/apiref.html#distutils.dir_util.copy_tree
            #   and
            #    https://docs.python.org/3.5/library/shutil.html
            #   For now, this only works if only the top level directory
            #   exists
            pass
        elif handle_existing == 'replace':
            # delete it; otherwise, exception will be raised by shutil.copytree
            if os.path.isdir(dir_to_create):
                shutil.rmtree(dir_to_create)
            else:
                # this really shouldn't ever be the case
                os.remove(dir_to_create)
            os.mkdir(dir_to_create)
        else:
            raise BlueSkyConfigurationError("Invalid value for "
                "handle_existing config option: {}".format(
                handle_existing))

    else:
        # create fresh empty dir
        os.makedirs(dir_to_create)

    return dir_to_create