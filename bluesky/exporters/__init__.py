"""bluesky.exporters"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import os
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

    def _bundle(self, fires_manager, dest, create_tarball=False):
        run_id = self._get_run_id(fires_manager)

        # create destination dir (to contain output dir) if necessary
        if not os.path.exists(dest):
            os.makedirs(output_dir)

        output_dir = os.path.join(dest, run_id)
        if os.path.exists(output_dir):
            if self.config('do_not_overwrite'):
                raise RuntimeError("{} already exists".format(output_dir))
            else:
                # delete it; otherwise, expection will be raised by shutil.copytree
                shutil.rmtree(output_dir)

        json_output_filename = self.config('json_output_filename') or 'output.json'
        with open(os.path.join(output_dir, json_output_filename), 'w') as f:
            f.write(json.dumps(fires_manager.dump()))

        for k in ['dispersion', 'visualization']:
            d = getattr(fires_manager, k):
            if d and d.get('output', {}).get('directory'):
                shutil.copytree(d['output']['directory'],
        # TODO: copy all other extra_imports into temp dir (under module-specific
        #  subdirs), tarball it,
        # TODO: create tarball aand return tarball name, if create_tarball==True,
        #  otherwise just return dir_name
