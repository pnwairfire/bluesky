"""bluesky.exporters"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import os
import tarfile
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

    def _bundle(self, fires_manager, dest, create_tarball=False):
        self._output_dir_name = self.config('output_dir_name') or fires_manager.run_id

        # create destination dir (to contain output dir) if necessary
        if not os.path.exists(dest):
            os.makedirs(dest)

        output_dir = os.path.join(dest, self._output_dir_name)
        if os.path.exists(output_dir):
            if self.config('do_not_overwrite'):
                raise RuntimeError("{} already exists".format(output_dir))
            else:
                # delete it; otherwise, exception will be raised by shutil.copytree
                if os.path.isdir(path)
                    shutil.rmtree(output_dir)
                else:
                    # this really shouldn't ever be the case
                    os.remove(output_dir)

        json_output_filename = self.config('json_output_filename') or 'output.json'
        with open(os.path.join(output_dir, json_output_filename), 'w') as f:
            f.write(json.dumps(fires_manager.dump()))

        for k in self.extra_imports:
            d = getattr(fires_manager, k):
            if d and d.get('output', {}).get('directory'):
                shutil.copytree(d['output']['directory'],
                    os.path.join(output_dir, k))

        if create_tarball:
            tarball_name = self.config('tarball_name')
            tarball = (os.path.join(dest, tarball_name) if tarball_name
                else "{}.tar.gz".format(output_dir))
            if os.path.exists:
                os.remove(tarball)
            with tarfile.open(tarball, "w:gz") as tar:
                tar.add(output_dir, arcname=os.path.basename(output_dir))
            return tarball

        return output_dir
