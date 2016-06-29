#!/usr/bin/env python

"""test_regression.py - regression test for a subset of the bsp modules

Note: this test is called test_regression so that it's picked up by py.test.
"""

__author__ = "Joel Dubowy"

import copy
import csv
import glob
import logging
import os
import subprocess
import sys
import traceback
import uuid

from pyairfire import scripting

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
# app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
#    os.path.abspath(__file__)))))
# sys.path.insert(0, app_root)

# We're running bluesky via the package rather than by running the bsp script
# to allow breaking into the code (with pdb)
from bluesky import models

# TODO: rename this script

# TODO: use a regression testing framework?

MODULES = [ os.path.basename(m.rstrip('/'))
    for m in glob.glob(os.path.join(os.path.dirname(__file__), '*'))]

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
    $ ./test/regression/all/test_regression.py -m emissions
"""


def check(actual, expected_partials, expected_totals):
    success = True
    #TODO: implement
    return success

def run_module(module):
    #TODO: implement
    pass

def run(args):
    if args.module:
        return run_module(module)
    else:
        success = True
        for module in MODULES:
            success = success and run_module(module)
    return success

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

    sys.exit(int(not success))