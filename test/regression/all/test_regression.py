#!/usr/bin/env python

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
import subprocess
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

MODULES = [ os.path.basename(m.rstrip('/'))
    for m in glob.glob(os.path.join(os.path.dirname(__file__), '*'))
    if os.path.isdir(m) and not os.path.basename(m).startswith('__')]  # catches '__pycache__' dir

REQUIRED_ARGS = [
]

OPTIONAL_ARGS = [
    {
        'short': '-module',
        'long': '--module',
        'help': 'options "{}"'.format(" or ".join(MODULES))
    }
]

EXAMPLES_STR = """

Examples:

    $ ./test/regression/all/test_regression.py
    $ ./test/regression/all/test_regression.py --log-level=DEBUG -m emissions
"""

def check_value(expected, actual):
    if type(expected) != type(actual):
        return False

    if type(expected) == dict:
        if set(expected.keys()) != set(actual.keys()):
            return False
        for k in expected:
            if not check_value(expected[k], actual[k]):
                return False
        return True

    elif type(expected) == list:
        if len(expected) != len(actual):
            return False
        for i in range(len(expected)):
            if not check_value(expected[i], actual[i]):
                return False
        return True

    elif type(expected) == float:
        try:
            # if failure, we want to return False rather than have AssertionError raised
            assert_approx_equal(expected, actual)
        except AssertionError:
            return False
        return True

    else:
        return expected == actual


def check(expected, actual):
    success = True
    expected.pop('runtime')
    actual.pop('runtime')
    # TODO: cherry pick other fields to check
    if len(expected['fire_information']) != len(actual['fire_information']):
        return False

    for i in range(len(expected['fire_information'])):
        expected['fire_information'][i].pop('error', None)
        actual['fire_information'][i].pop('error', None)
        if not check_value(expected['fire_information'][i], actual['fire_information'][i]):
            return False

    return True

def run_input(module, input_file):
    output_file = input_file.replace('input/', 'output/').replace(
        '.json', '-EXPECTED-OUTPUT.json')

    logging.debug('Running bsp on %s', input_file)
    try:
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
            logging.error('FAILED - %s - %s', input_file, e)
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
    return all([run_input(module, f) for f in files])

def test(module=None):
    modules = [module] if module else MODULES
    results = [run_module(module) for module in modules]
    logging.info('Summary:')
    for i, r in enumerate(results):
        logging.info(' %s: %s', modules[i], 'PASSED' if r else 'FAILED')
    assert all(results)

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    if args.module and args.module not in MODULES:
        logging.error("Module '%s' has no test data or is invalid", args.module)
        sys.exit(1)

    try:
        test(module=args.module)

    except Exception as e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        afscripting.utils.exit_with_msg(e)

    # No need to exit with code when we use the assertions in `test`, above.
    #  (script will return 0 if sucecss and 1 otherwise.)
    #sys.exit(int(not success))
