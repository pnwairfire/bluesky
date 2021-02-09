"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import itertools
import logging

from bluesky.config import Config
from bluesky import exceptions
from bluesky.locationutils import LatLng

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Looks up ecoregion for each location

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    fires_manager.processed(__name__, __version__)
    EcoregionRunner(fires_manager).run()


class EcoregionRunner(object):

    def __init__(self, fires_manager):
        self._fires_manager = fires_manager
        self._ecoregion_lookup = None

    @property
    def ecoregion_lookup(self):
        # lazy import EcoregionLookup
        if not self._ecoregion_lookup:
            from bluesky.ecoregion.lookup import EcoregionLookup
            implementation = Config().get('ecoregion', 'lookup_implementation')
            self._ecoregion_lookup = EcoregionLookup(implementation)
        return self._ecoregion_lookup

    def run(self):
        ecoregion_lookup = None # instantiate only if necessary
        for fire in self._fires_manager.fires:
            with self._fires_manager.fire_failure_handler(fire):
                for loc in fire.locations:
                    if not loc.get('ecoregion'):
                        try:
                            latlng = LatLng(loc)
                            loc['ecoregion'] = self.ecoregion_lookup.lookup(
                                latlng.latitude, latlng.longitude)

                            if not loc['ecoregion']:
                                logging.warning("Failed to look up ecoregion for "
                                    "{}, {}".format(latlng.latitude, latlng.longitude))

                        except Exception as e:
                            logging.warn(f"Failed to look up ecoregion for loc {loc}")
                            # TODO: raise exception unless configured not to fail
