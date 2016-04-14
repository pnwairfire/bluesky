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
                        "uri": "/data/fires/fire_locations.csv"
                    }
                ]
            }
        }
    }

Currently supported sources:  smartfire2
Currently supported types: file
Currently supported formats: CSV
"""

from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Loads fire data from one or more sources

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.debug("Running load module")
    successfully_loaded_sources = []
    try:
        for source in in fires_manager.get_config_value('load', 'sources', default='[]'):
            # TODO: use something like with fires_manager.fire_failure_handler(fire)
            #   to optionally skip invalid sources (sources that are insufficiently
            #   configured, don't have corresponding loader class, etc.) and source
            #   that fail to load
            try:
                loader = _import_loader(source)
                loaded_fires = loader.load()
                fires_manager.add_fires(loaded_fires)
                # TODO: add fires to fires_manager
                successfully_loaded_sources.append(source)
            except:
                if not fires_manager.get_config_value('skip_failed_sources'):
                    raise

            parsed_input = []
            fire_ingester = FireIngester()
            for fire in fires_manager.fires:
                with fires_manager.fire_failure_handler(fire):
                    parsed_input.append(fire_ingester.ingest(fire))

        fires_manager.processed(__name__, __version__)
    finally:
        fires_manager.processed(__name__, __version__,
            successfully_loaded_sources=successfully_loaded_sources)

def _import_loader(source):
    if any([not source.get(k) for k in ['name', 'format', 'type']]):
        raise BlueSkyConfigurationError(
            "Specify 'name', 'format', and 'type' for each source of fire data")

    try:
        loader_module = importlib.import_module('bluesky.loaders.{}.{}'.format(
            source['name'].lower(), source['format'].lower()))
    except ImportError, e:
        raise BlueSkyConfigurationError("Invalid source and/or format: {},{}".format(
            source['name'], source['format']))

    loader = getattr(loader_module, '{}Loader'.format(source['type'].capitalize()))
    if not loader:
        raise BlueSkyConfigurationError("Invalid source type: {},{},{}".format(
            source['name'], source['format'], source['type']))

    return loader

