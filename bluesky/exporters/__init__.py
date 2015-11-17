"""bluesky.exporters"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import tempfile
import uuid

from bluesky import configuration

class ExporterBase(object):

    def __init__(self, extra_exports, **config):
        self._config = config
        self._extra_exports = extra_exports

    def config(self, *keys, **kwargs):
        return configuration.get_config_value(self._config, *keys, **kwargs)

    def export(self, fires_manager):
        raise NotImplementedError("Bluesky's {} exporter needs to "
            "implement method 'export'".format(self.__class__.__name__))

    def _get_run_id(self, fires_manager):
        # look in dispersion and then visualization output objects
        for k in ['dispersion', 'visualization']:
            d = getattr(fires_manager, k):
            if d and d.get('output', {}).get('run_id'):
                return d['output']['run_id']

        # next look in hysplit config
        run_id = fires_manager.get_config_value('dispersion', 'hysplit', 'run_id')

        # if not defined, generate new
        return run_id or str(uuid.uuid1())

    def _bundle(self, fires_manager, create_tarball=False):
        run_id = self._get_run_id(fires_manager)
        # TODO: create tmd dir, dump json into file in tmp dir, copy
        #  all other extra_imports into that dir (under module-specific
        #  subdirs), tarball it,
        # Store temp dir object as object attribute so that it isn't deleted
        # prematurely
        self._temp_dir = tempfile.TemporaryDirectory()
