"""bluesky.modules.load

Example configuration:

    {
        "config":{
            "load": {
                "sources": [
                    {
                        "name": "smartfire2",
                        "format": "CSV",
                        "type": "file",
                        "file": "/bluesky/data/fires/fire_locations_%Y%m%d.csv",
                        "events_file": "/bluesky/data/fires/fire_events_%Y%m%d.csv"
                    }
                ]
            }
        }
    }

or, on the command line:

    bsp --no-input -B skip_failed_fires=True -J load.sources='[{
        "name":"smartfire2",
        "format":"CSV",
        "type":"file",
        "file": "/bluesky/data/fires/fire_locations_{yesterday:%Y%m%d}.csv",
        "events_file": "/bluesky/data/fires/fire_events_{yesterday:%Y%m%d}.csv"
    }]' load -o out.json

Currently supported sources:  smartfire2
Currently supported types: file
Currently supported formats: CSV
"""

import importlib
import logging

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
    logging.info("Running load module")
    successfully_loaded_sources = []
    sources = fires_manager.get_config_value('load', 'sources', default=[])
    if not sources:
        raise BlueSkyConfigurationError("No sources specified for load module")
    try:
        for source in sources:
            # TODO: use something like with fires_manager.fire_failure_handler(fire)
            #   to optionally skip invalid sources (sources that are insufficiently
            #   configured, don't have corresponding loader class, etc.) and source
            #   that fail to load
            try:
                loader = _import_loader(source)
                loaded_fires = loader(**source).load()
                fires_manager.add_fires(loaded_fires)
                # TODO: add fires to fires_manager
                successfully_loaded_sources.append(source)
            except:
                if not fires_manager.get_config_value('skip_failed_sources'):
                    raise
    finally:
        fires_manager.processed(__name__, __version__,
            successfully_loaded_sources=successfully_loaded_sources)

def _import_loader(source):
    if any([not source.get(k) for k in ['name', 'format', 'type']]):
        raise BlueSkyConfigurationError(
            "Specify 'name', 'format', and 'type' for each source of fire data")

    try:
        loader_module = importlib.import_module(
            'bluesky.loaders.{}'.format(source['name'].lower()))
    except ImportError as e:
        raise BlueSkyConfigurationError(
            "Invalid source: {}".format(source['name']))

    loader = getattr(loader_module, '{}{}Loader'.format(
        source['format'].capitalize(), source['type'].capitalize()))
    if not loader:
        raise BlueSkyConfigurationError(
            "Invalid source format or type: {},{},{}".format(
            source['name'], source['format'], source['type']))

    return loader

