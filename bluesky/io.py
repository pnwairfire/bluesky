"""bluesky.io"""

__author__ = "Joel Dubowy"

import logging
import os
import shutil

from pyairfire.io import *

from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)

__all__ = [
    "create_dir_or_handle_existing",
    "wait_for_availability"
]

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


INVALID_WAIT_CONFIG_MSG = ("'strategy', 'time', 'max_attempts' "
    "must all be defined if waiting for a resource")
INVALID_WAIT_STRATEGY_MSG = "Wait strategy must be 'fixed' or 'backoff'"
INVALID_WAIT_TIME_MSG = "Wait time must be positive number"
INVALID_WAIT_MAX_ATTEMPTS_MSG = "Wait max_attempts must be positive integer"

def wait_for_availability(config):
    # wait_config can be undefined, but if it is defined, it must include
    # strategy, time, and max_attempts.
    if config and any([not config.get(k)
            for k in ('strategy','time','max_attempts'))]):
        raise BlueSkyConfigurationError(INVALID_WAIT_CONFIG_MSG)
    if config['strategy'] not in ('fixed', 'backoff'):
        raise BlueSkyConfigurationError(INVALID_WAIT_STRATEGY_MSG)
    if not isinstance(config['time'], (int, float)) or config['time'] <= 0.0:
        raise BlueSkyConfigurationError(INVALID_WAIT_TIME_MSG)
    if (not isinstance(config['max_attempts'], int)
            or config['max_attempts'] <= 0):
        raise BlueSkyConfigurationError(INVALID_WAIT_MAX_ATTEMPTS_MSG)

    def decorater(f):
        if config:
            def decorated(*args, **kwargs):
                sleep_time = config['time']
                attempts = 0
                while True:
                    try:
                        f(*args, **kwargs)

                    except BlueSkyUnavailableResourceError as e:
                        attempts += 1
                        if attempts == config['max_attempts']:
                            raise

                        time.sleep(sleep_time)
                        if config['strategy'] == 'backoff':
                            sleep_time *= 2

                    else:
                        break

            return decorated
        else:
            return f
