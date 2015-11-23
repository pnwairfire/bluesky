"""bluesky.exporters"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import json
import os
import shutil
import tarfile
import tempfile

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
                if os.path.isdir(output_dir):
                    shutil.rmtree(output_dir)
                else:
                    # this really shouldn't ever be the case
                    os.remove(output_dir)

        # create fresh empty dir
        os.mkdir(output_dir)

        json_output_filename = self.config('json_output_filename') or 'output.json'
        with open(os.path.join(output_dir, json_output_filename), 'w') as f:
            fires_manager.dumps(output_stream=f)

        r = {
            'output_json': json_output_filename
        }

        dirs_to_copy = {}
        for k in self._extra_exports:
            d = getattr(fires_manager, k)
            if d and d.get('output', {}).get('directory'):
                dirs_to_copy[d['output']['directory']] = dirs_to_copy.get(
                    d['output']['directory'], [])
                dirs_to_copy[d['output']['directory']].append(k)
        for directory, extra_imports in dirs_to_copy.items():
            new_dirname = '-'.join(extra_imports)
            shutil.copytree(directory, os.path.join(output_dir, new_dirname))
            for k in extra_imports:
                r[k] = {'sub_dir': new_dirname}
                processor = getattr(self, '_process_{}'.format(k), None)
                if processor:
                    processor(getattr(fires_manager, k), r)

        if create_tarball:
            tarball_name = self.config('tarball_name')
            tarball = (os.path.join(dest, tarball_name) if tarball_name
                else "{}.tar.gz".format(output_dir))
            if os.path.exists(tarball):
                os.remove(tarball)
            with tarfile.open(tarball, "w:gz") as tar:
                tar.add(output_dir, arcname=os.path.basename(output_dir))
            r['tarball'] = tarball
        else:
            r['directory'] = output_dir

        return r

    def _process_dispersion_(self, d, r):
        # TODO: update r with relative location of nc file, etc.)
        # TODO: look in 'd' to see what model of dispersion was run, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        # TODO: glob r['dispersion']['sub_dir'] for .nc file
        # TODO: Support option to rename nc file; other files too?
        pass

    def _process_visualization(self, d, r):
        # TODO: update r with relative location of kmz, images, etc.
        pass