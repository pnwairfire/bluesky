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

from pyairfire import scripting

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
   os.path.abspath(__file__)))))
sys.path.insert(0, app_root)

# We're running bluesky via the package rather than by running the bsp script
# to allow breaking into the code (with pdb)
from bluesky import models

MODULES = [ os.path.basename(m.rstrip('/'))
    for m in glob.glob(os.path.join(os.path.dirname(__file__), '*'))
    if os.path.isdir(m)]

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


def check(expected, actual):
    success = True
    expected.pop('runtime')
    actual.pop('runtime')
    # TODO: cherry pick other fields to check
    return expected['fire_information'] == actual['fire_information']

def run_input(module, input_file):
    output_file = input_file.replace('input/', 'output/').replace(
        '.json', '-EXPECTED-OUTPUT.json')

    logging.info('Running bsp on %s', input_file)
    try:
        fires_manager = models.fires.FiresManager()
        fires_manager.loads(input_file=input_file)
        fires_manager.modules = [module]
        fires_manager.run()
    except Exception as e:
        # if output file doesn't exist, it means this expection was expected
        # TODO: confirm that this is valid logic
        if os.path.isfile(output_file):
            logging.error('Failed run: %s', e)
            return False
        else:
            logging.debug('Expected run failure')
            return True

    logging.info('Loading expected output file %s', output_file)
    with open(output_file, 'r') as f:
        expected = json.loads(f.read())
    # dumps and loads actual to convert datetimest, etc.
    actual = json.loads(json.dumps(fires_manager.dump(),
        cls=models.fires.FireEncoder))
    success = check(expected, actual)
    logging.info('Success!') if success else logging.error('FAILED')
    return success

def run_module(module):
    files = [os.path.abspath(f) for f in glob.glob(os.path.join(
        os.path.dirname(__file__), module, 'input', '*')) ]
    return all([run_input(module, f) for f in files])

def run(args):
    if args.module:
        return run_module(args.module)
    else:
        return all([run_module(module) for module in MODULES])

if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    if args.module and args.module not in MODULES:
        logging.error("Module '%s' has no test data or is invalid", args.module)
        sys.exit(1)

    try:
        success = run(args)

    except Exception as e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        scripting.utils.exit_with_msg(e)

    # No need to exit with code when we use the assertion here.
    #  will return 0 if sucecss and 1 otherwise
    #sys.exit(int(not success))
    assert success
