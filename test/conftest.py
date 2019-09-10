import sys, os

import pytest

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_root)

from bluesky.config import Config

@pytest.fixture(scope="function")
def reset_config():
    Config().reset()
    return Config()

# def setup_method(self, method):
#     """setup_method is invoked for every test method of a class.
#     """
#     Config().reset()
