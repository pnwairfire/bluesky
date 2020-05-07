#!/usr/bin/env python3

"""test_regression.py - regression test for a subset of the bsp modules

Note: this test is called test_regression so that it's picked up by py.test.

TODO: use a regression testing framework?
TODO: rename this script
"""

__author__ = "Joel Dubowy"

import glob
import json
import logging
import os
import sys
import traceback

import afscripting
from numpy.testing import assert_approx_equal

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
   os.path.abspath(__file__)))))
sys.path.insert(0, app_root)

# We're running bluesky via the package rather than by running the bsp script
# to allow breaking into the code (with pdb)
from bluesky import models, exceptions
from bluesky.config import Config

MODULES = [ os.path.basename(m.rstrip('/'))
    for m in glob.glob(os.path.join(os.path.dirname(__file__), '*'))
    if os.path.isdir(m) and not os.path.basename(m).startswith('__')]  # catches '__pycache__' dir

REQUIRED_ARGS = [
]

OPTIONAL_ARGS = [
    {
        'short': '-m',
        'long': '--module',
        'help': 'options "{}"'.format(" or ".join(MODULES))
    }
]

EXAMPLES_STR = """

Examples:

    $ ./test/regression/all/test_regression.py
    $ ./test/regression/all/test_regression.py --log-level=DEBUG -m emissions
"""

RED = '\x1b[31m' # red
YELLOW = '\x1b[33m' # yellow
GREEN = '\x1b[32m' # green
WHITE = '\x1b[0m' # normal

def add_coloring_to_emit_ansi(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if(levelno>=50): # FATAL
            color = RED
        elif(levelno>=40): # ERROR
            color = RED
        elif(levelno>=30): # WARNING
            color = YELLOW
        # elif(levelno>=20): # INFO
        #     color = GREEN
        # elif(levelno>=10): # DEBUG
        #     color = '\x1b[35m' # pink
        else:
            color = WHITE
        args[1].msg = color + args[1].msg +  WHITE
        #print "after"
        return fn(*args)
    return new

def set_logging_color(args):
    if not args.log_file:
        logging.StreamHandler.emit = add_coloring_to_emit_ansi(
            logging.StreamHandler.emit)


def check_value(expected, actual, *keys_for_error_log):
    if type(expected) != type(actual):
        logging.error("types don't match: %s vs. %s  ('%s')",
            type(expected), type(actual), "' > '".join(keys_for_error_log))
        return False

    if type(expected) == dict:
        if set(expected.keys()) != set(actual.keys()):
            logging.error("Keys don't match (for '%s'): \n  EXPECTED: %s\n  ACTUAL:   %s",
                "' > '".join(keys_for_error_log),
                ','.join(sorted(list(set(expected.keys())))),
                ','.join(sorted(list(set(actual.keys())))))
            return False
        # check all; don't bail after first difference  (so that
        # we see all differing values in output)
        results = [check_value(expected[k], actual[k],
            *(keys_for_error_log + (k,))) for k in expected]
        return all(results)

    elif type(expected) == list:
        if len(expected) != len(actual):
            logging.error("list lengths don't match  ('%s')",
                "' > '".join(keys_for_error_log))
            return False
        for i in range(len(expected)):
            if not check_value(expected[i], actual[i], *(keys_for_error_log + (str(i),) )):
                return False
        return True

    elif type(expected) == float:
        try:
            # if failure, we want to return False rather than have AssertionError raised
            assert_approx_equal(expected, actual)
        except AssertionError:
            logging.error("Float values don't match: %s vs. %s  ('%s')",
                expected, actual, "' > '".join(keys_for_error_log))
            return False
        return True

    else:
        if expected == actual:
            return True
        else:
            logging.error("Values don't match: %s vs. %s  ('%s')",
                expected, actual, "' > '".join(keys_for_error_log))
            return False


def check(expected, actual):
    success = True
    expected.pop('runtime')
    actual.pop('runtime')
    # TODO: cherry pick other fields to check
    if len(expected['fires']) != len(actual['fires']):
        return False

    for i in range(len(expected['fires'])):
        expected['fires'][i].pop('error', None)
        actual['fires'][i].pop('error', None)
        if not check_value(expected['fires'][i], actual['fires'][i]):
            return False

    return True

def run_input(module, input_file):
    output_file = input_file.replace('input/', 'output/').replace(
        '.json', '-EXPECTED-OUTPUT.json')
    config_file = input_file.replace('input/', 'config/').replace(
        '.json', '-CONFIG.json')

    with open(config_file) as f:
        config = json.loads(f.read()).get('config')

    logging.debug('Running bsp on %s', input_file)
    try:
        if 'skip_failed_fires' not in config:
            # regression test output data was generated when
            # skip_failed_fires defaulted to false
            config['skip_failed_fires'] = False

        Config().set(config)
        fires_manager = models.fires.FiresManager()
        fires_manager.loads(input_file=input_file)
        fires_manager.modules = [module]
        fires_manager.run()
    except exceptions.BlueSkyModuleError as e:
        # The error was added to fires_manager's meta data, and will be
        # included in the output data
        pass
    except Exception as e:
        # if output file doesn't exist, it means this expection was expected
        # TODO: confirm that this is valid logic
        if os.path.isfile(output_file):
            logging.error('FAILED - %s - %s', input_file, str(e))
            return False
        else:
            logging.debug('Caught expected exception')
            return True

    try:
        logging.debug('Loading expected output file %s', output_file)
        with open(output_file, 'r') as f:
            expected = json.loads(f.read())
    except FileNotFoundError as e:
        logging.error('FAILED - %s - missing output file', input_file)
        return False

    # dumps and loads actual to convert datetimest, etc.
    actual = json.loads(json.dumps(fires_manager.dump(),
        cls=models.fires.FireEncoder))
    success = check(expected, actual)
    logging.info('PASSED - %s', input_file) if success else logging.error('FAILED - %s', input_file)
    return success

def run_module(module):
    files = [os.path.abspath(f) for f in glob.glob(os.path.join(
        os.path.dirname(__file__), module, 'input', '*')) ]
    results = [run_input(module, f) for f in files]
    logging.info("Results for %s", module)
    for i, r in enumerate(results):
        logging.info(' %s: %s%s%s', files[i],
            GREEN if r else RED, 'PASSED' if r else 'FAILED', WHITE)
    return all(results)

def test(module=None):
    modules = [module] if module else MODULES
    results = [run_module(module) for module in modules]
    logging.info('Summary:')
    for i, r in enumerate(results):
        logging.info(' %s: %s%s%s', modules[i],
            GREEN if r else RED, 'PASSED' if r else 'FAILED', WHITE)
    assert all(results)

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    if args.module and args.module not in MODULES:
        logging.error("Module '%s' has no test data or is invalid", args.module)
        sys.exit(1)

    set_logging_color(args)

    try:
        test(module=args.module)

    except Exception as e:
        logging.error(str(e))
        logging.debug(traceback.format_exc())
        afscripting.utils.exit_with_msg(str(e))

    # No need to exit with code when we use the assertions in `test`, above.
    #  (script will return 0 if sucecss and 1 otherwise.)
    #sys.exit(int(not success))
