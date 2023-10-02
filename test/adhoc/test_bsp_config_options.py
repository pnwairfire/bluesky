#!/usr/bin/env python3

"""Tests bsp's -c' and '-C' options

TODO: test error cases ('-c' set to non-existent file; invalid values for
    '--bool-config-value', '--int-config-value', '--float-config-value';
    config conflicts; etc.)
"""

import datetime
import json
import logging
import os
import subprocess
import sys
import tempfile

from pytest import raises

from bluesky import datetimeutils
from bluesky.config import DEFAULTS

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, ROOT_DIR) # in case this script is run outside of py.test
BSP = os.path.join(ROOT_DIR, 'bin/bsp')


INPUT = {
    "run_id": 'abcdefg123',
    "fires": [],
    "run_config": {  # 'run_config' is ignored in input data
        "foobar": 12312
    }
}

CONFIG_0 = {
    "config": {
        "foo": {
            "a": 111,
            "b": 222,
            "c": 333,
            "d": 444
        },
        'echo_run_id': '{run_id}'
    }
}

CONFIG_1 = {
    "config": {
        "foo": {
            "b": 2222,
            "c": 3333,
            "d": 4444,
            "bb": "bb"
        },
        "bar": {
            "b": "b"
        },
        "b": "b",
        "e": '{run_id}__{_run_id}'
    }
}

CONFIG_2 = {
    "run_config": { # either 'config' or 'run_config' is allowed
        "foo": {
            "c": 33333,
            "d": 44444,
            "cc": "cc"
        },
        "baz": {
            "c": "c"
        },
        "c": "c"
    }
}

# Note: "-C foo.d=444444 -C foo.dd=dd -C boo.d=d -C d=d "
#  and "-B dbt=true -B dbf=0 -I di=23 -F df=123.23"
#  and "-C dci=23 -C dcf=123.23"
#  will be specified on the command line

EXPECTED = {
    "run_config": dict(DEFAULTS, **{
        "foo": {
            "a": 111,
            "b": 2222,
            "c": 33333,
            "d": "444444", # because it was set on command line
            "bb": "bb",
            "cc": "cc",
            "dd": "dd"
        },
        'echo_run_id': 'abcdefg123',
        "bar": {
            "b": "b"
        },
        "baz": {
            "c": "c"
        },
        "boo": {
            "d": "d"
        },
        "b": "b",
        "c": "c",
        "d": "d",
        "dbt": True,
        "dbf": False,
        "di": 23,
        "df": 123.23,
        "dci": "23",
        "dcf": "123.23",
        "e": 'abcdefg123__{_run_id}',
        #"f": 'sdfdsf__abcdefg123'
    }),
    "fires": []
}

# smoke ready config defaults have datetime wildcards; call fill-in code
# on all of EXPECTED, in case future config params also have wildcards
def replace_config_wildcards(val):
    if isinstance(val, dict):
        for k in val:
            val[k] = replace_config_wildcards(val[k])
    elif isinstance(val, list):
        val = [replace_config_wildcards(v) for v in val]
    elif hasattr(val, 'lower'):  # i.e. it's a string
        if val:
            # first, fill in any datetime control codes or wildcards
            val = datetimeutils.fill_in_datetime_strings(val)
    return val
EXPECTED['run_config'] = replace_config_wildcards(EXPECTED['run_config'])

input_file = tempfile.NamedTemporaryFile(mode='w+t')
input_file.write(json.dumps(INPUT))
input_file.flush()

config_0_file = tempfile.NamedTemporaryFile(mode='w+t')
config_0_file.write(json.dumps(CONFIG_0))
config_0_file.flush()

config_1_file = tempfile.NamedTemporaryFile(mode='w+t')
config_1_file.write(json.dumps(CONFIG_1))
config_1_file.flush()

config_2_file = tempfile.NamedTemporaryFile(mode='w+t')
config_2_file.write(json.dumps(CONFIG_2))
config_2_file.flush()

cmd_args = [
    BSP, '-i', input_file.name,
    '--log-level', 'DEBUG',
    '-c', config_0_file.name,
    '-c', config_1_file.name,
    '-c', config_2_file.name,
    '-C', 'foo.d=444444',
    '-C', 'foo.dd=dd',
    '-C', 'boo.d=d',
    '-C', 'd=d',
    #'-C', 'f="sdfdsf__{run_id}"'
    '-B', 'dbt=true',
    '-B', 'dbf=0',
    '-I', 'di=23',
    '-F', 'df=123.23',
    '-C', 'dci=23',
    '-C', 'dcf=123.23'

]
output = subprocess.check_output(cmd_args)
actual = json.loads(output.decode())
actual.pop('runtime')
logging.basicConfig(level=logging.INFO)
logging.info("actual:   {}".format(actual))
logging.info("expected: {}".format(EXPECTED))
today = actual.pop('today')
assert today == datetime.datetime.utcnow().strftime('%Y-%m-%dT00:00:00')
#assert actual == EXPECTED
assert set(actual.keys()) == set(['run_config', 'fires', 'run_id', 'counts', 'bluesky_version'])
assert actual['fires'] == EXPECTED['fires']
assert set(actual['run_config'].keys()) == set(EXPECTED['run_config'].keys())
for k in actual['run_config'].keys():
    # if actual['run_config'][k] != EXPECTED['run_config'][k]:
    #     import pdb;pdb.set_trace()
    logging.info('Checking output config key %s', k)
    assert actual['run_config'][k] == EXPECTED['run_config'][k]


# Now check that specifying 'config' in input data causes failure
INPUT['config'] = INPUT.pop('run_config')
invalid_input_file = tempfile.NamedTemporaryFile(mode='w+t')
invalid_input_file.write(json.dumps(INPUT))
invalid_input_file.flush()
cmd_args[2] = invalid_input_file.name
with raises(subprocess.CalledProcessError) as e:
    output = subprocess.check_output(cmd_args)
print("\n*** Correctly failed due to 'config' in input data ***\n")

print("\n*** PASSED ***\n")