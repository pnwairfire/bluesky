#!/usr/bin/env python

"""Tests bsp's -c' and '-C' options
"""

import json
import logging
import os
import subprocess
import tempfile

BSP = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), '../../bin/bsp'))

INPUT = {
    "config": {
        "foo": {
            "a": 111,
            "b": 222,
            "c": 333,
            "d": 444
        }
    },
    "fire_information": []
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
        "b": "b"
    }
}

CONFIG_2 = {
    "config": {
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

# Note: "-C foo.d=444444 -C foo.dd=dd -C boo.d=d -C d=d" will be specified on the command line

EXPECTED = {
    "config": {
        "foo": {
            "a": 111,
            "b": 2222,
            "c": 33333,
            "d": "444444", # because it was set on command line
            "bb": "bb",
            "cc": "cc",
            "dd": "dd"
        },
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
        "d": "d"
    },
    "fire_information": []
}

input_file = tempfile.NamedTemporaryFile()
input_file.write(json.dumps(INPUT))
input_file.flush()

config_1_file = tempfile.NamedTemporaryFile()
config_1_file.write(json.dumps(CONFIG_1))
config_1_file.flush()

config_2_file = tempfile.NamedTemporaryFile()
config_2_file.write(json.dumps(CONFIG_2))
config_2_file.flush()

cmd_args = [
    BSP, '-i', input_file.name,
    '-c', config_1_file.name, '-c', config_2_file.name,
    '-C', 'foo.d=444444', '-C', 'foo.dd=dd',
    '-C', 'boo.d=d', '-C', 'd=d'
]
output = subprocess.check_output(cmd_args)
logging.basicConfig(level=logging.INFO)
logging.info("actual:   {}".format(output))
logging.info("expected: {}".format(EXPECTED))
assert EXPECTED == json.loads(output)
