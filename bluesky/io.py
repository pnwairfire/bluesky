"""bluesky.io"""

__author__ = "Joel Dubowy"

import logging
import io
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import time

from pyairfire.io import *

from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError,
    BlueSkySubprocessError
)

__all__ = [
    "create_dir_or_handle_existing",
    "wait_for_availability",
    "capture_stdout",
    "SubprocessExecutor",
    "create_tarball"
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

    def __enter__(self):
        sys.stdout = io.StringIO()
        # returning sys.stdout isn't necessary, since user could
        # just use a reference to sys.stdout directly, but it's for
        # convenience and hopefully more intuitive usage
        return sys.stdout

    def __exit__(self, e_type, value, tb):
        sys.stdout = sys.__stdout__


class SubprocessExecutor(object):
    """Wraps command execution in order to capture
    and optionally log stdout and stderr output

    To adhoc test:

        python3 -c 'from bluesky import io; io.SubprocessExecutor().execute("echo \"hello\"")'
    """

    def __init__(self, stdout_log_level=logging.DEBUG):
        self._stdout_log_level = stdout_log_level

    def execute(self, *args, cwd=None, realtime_logging=True):
        self._set_cmd_args(args)

        try:
            f = (self._execute_with_real_time_logging if realtime_logging
                else self._execute_with_logging_after)
            f(cwd)

        except subprocess.CalledProcessError as e:
            # note e.output and e.stdout are aliases
            self._log(e.output)
            self._log(e.stderr, is_stdout=False)
            # Note: not logging e.cmd and e.returncode, since they'll
            #   be logged by top level exception handler
            raise BlueSkySubprocessError(e)

        except FileNotFoundError as e:
            self._log(e.strerror, is_stdout=False)
            raise BlueSkySubprocessError(e)

        except BlueSkySubprocessError:
            # any stderr will have been logged; just reraise
            raise

        except Exception as e:
            raise BlueSkySubprocessError(e)

    def _set_cmd_args(self, args):
        # Support three ways of being called:
        if len(args) == 1:
            # e.g. SubprocessExecutor().execute('ls foo')
            if hasattr(args[0], 'split'):
                self._cmd_args = shlex.split(args[0])
                self._cmd_str = args[0]

            # e.g. SubprocessExecutor().execute(['ls', 'foo'])
            elif hasattr(args[0], 'append'):
                self._cmd_args = args[0]
                self._cmd_str = ' '.join(args[0])

            else:
                raise ValueError(
                    "Invalid args for SubprocessExecutor.execute: {}".format(args))

        # e.g. SubprocessExecutor().execute('ls', 'foo')
        else:
            self._cmd_args = args
            # TODO: use shlex.join after upgrading to python>=3.8
            self._cmd_str = ' '.join(args)

        logging.info('Executing {}'.format(self._cmd_str))
        self._executable = os.path.basename(self._cmd_args[0])

    def _execute_with_real_time_logging(self, cwd):
        process = subprocess.Popen(self._cmd_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, cwd=cwd, universal_newlines=True)

        ret_val = None

        while ret_val is None:
            # There will be at least one printed line - minimally,
            # a single newline
            line = process.stdout.readline()
            if line != "":
                self._log(line)

            ret_val = process.poll()

        if ret_val > 0:
            self._log(process.stderr.read(), is_stdout=False)
            raise BlueSkySubprocessError()

    def _execute_with_logging_after(self, cwd):
        # Use check_output so that output isn't sent to stdout
        # TODO: capture stdout and stderr separately, so that
        #   different log levels can be used.
        output = subprocess.check_output(self._cmd_args,
            stderr=subprocess.STDOUT, cwd=cwd, universal_newlines=True)
        self._log(output)

    def _log(self, output, is_stdout=True):
        if output:
            log_level = self._stdout_log_level if is_stdout else logging.ERROR
            for line in output.strip().split('\n'):
                logging.log(log_level, '%s: %s', self._executable, line)


def create_tarball(output_dir, tarball_pathname=None):
    tarball_pathname = tarball_pathname or "{}.tar.gz".format(
        output_dir.rstrip('/'))
    if os.path.exists(tarball_pathname):
        os.remove(tarball_pathname)
    with tarfile.open(tarball_pathname, "w:gz") as tar:
        tar.add(output_dir, arcname=os.path.basename(output_dir))
    return tarball_pathname
