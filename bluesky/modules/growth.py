"""bluesky.modules.growth

Example configuration:

    {
        "config": {
            "growth": {
                "model": "persistence",
                "persistence": {
                    "date_to_persist": "2020-09-10",
                    "days_to_persist": 4,
                    "truncate": false
                }
            }
        }
    }

"""

import importlib
import logging

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Loads fire data from one or more sources

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    model = Config().get('growth', 'model') # defaults to 'persistence'
    try:
        growth_module = importlib.import_module(
            'bluesky.growers.{}'.format(model.lower()))
    except ImportError as e:
        raise BlueSkyConfigurationError(
            "Invalid growth module: {}".format(model))

    getattr(growth_module, 'Grower')(fires_manager).grow()
