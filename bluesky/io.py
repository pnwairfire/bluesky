"""bluesky.io"""

__author__ = "Joel Dubowy"

import logging
import io
import os
import shutil
import sys
import time

from pyairfire.io import *

from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)

__all__ = [
    "create_dir_or_handle_existing",
    "wait_for_availability",
    "capture_stdout"
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
    # config can be undefined, but if it is defined, it must include
    # strategy, time, and max_attempts.
    if config:
        if any([not config.get(k)
                for k in ('strategy', 'time', 'max_attempts')]):
            raise BlueSkyConfigurationError(INVALID_WAIT_CONFIG_MSG)

        if config['strategy'] not in ('fixed', 'backoff'):
            raise BlueSkyConfigurationError(INVALID_WAIT_STRATEGY_MSG)
        if not isinstance(config['time'], (int, float)) or config['time'] <= 0.0:
            raise BlueSkyConfigurationError(INVALID_WAIT_TIME_MSG)
        if (not isinstance(config['max_attempts'], int)
                or config['max_attempts'] <= 0):
            raise BlueSkyConfigurationError(INVALID_WAIT_MAX_ATTEMPTS_MSG)

    def decorator(f):
        if config:
            def decorated(*args, **kwargs):
                sleep_time = config['time']
                attempts = 0

                while True:
                    try:
                        return f(*args, **kwargs)

                    except BlueSkyUnavailableResourceError as e:
                        attempts += 1
                        if attempts == config['max_attempts']:
                            logging.info(
                                "Resource doesn't exist. Reached max attempts."
                                " (%s)", e)
                            raise

                        logging.info("Resource doesn't exist. Will attempt "
                            "again in %s seconds. (%s)", sleep_time, e)
                        time.sleep(sleep_time)
                        if config['strategy'] == 'backoff':
                            sleep_time *= 2

                    else:
                        break

            return decorated
        else:
            return f

    return decorator


class capture_stdout(object):
    """Context manager that redirects stdout to a stringIO buffer

    Note: could also write to dev null like:

        with open(os.devnull,"w") as devnull:
            sys.stdout = devnull
            ...

    but then we'd lose the output.

    TODO: make wirting to devnull an option, for situations
    where there is a large amount of output.

    TODO: move this to pyairfire.io
    """

    def __init__(self):
        self._buffer = io.StringIO()

    def __enter__(self):
        sys.stdout = self._buffer
        return self._buffer

    def __exit__(self, e_type, value, tb):
        sys.stdout = sys.__stdout__
        if e_type:
            self._fire['error'] = str(value)
        return True # return true even if there's an error
