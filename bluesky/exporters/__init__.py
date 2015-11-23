"""bluesky.exporters"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import fnmatch
import json
import os
import re
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

        # TODO: support options to dump fire and emissions information to csv
        #   (i.e. fire_locations.csv, fire_events.csv, and fire_emissions.csv)

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
                r[k] = {'sub_directory': new_dirname}
                processor = getattr(self, '_process_{}'.format(k), None)
                if processor:
                    processor(getattr(fires_manager, k), r)

        # TODO: support option to create symlinks (like link in root of bundle
        #  to KMZ, to images, etc.);  sym-links are preserved by tarball;
        #  add sym link information to r

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

    NETCDF_PATTERN = '*.nc'
    def _process_dispersion(self, d, r):
        # TODO: look in 'd' to see what model of dispersion was run, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        # TODO: Support option to rename nc file; other files too?
        netcdfs = self._find_files(d['output']['directory'], self.NETCDF_PATTERN)
        if netcdfs:
            if len(netcdfs) > 1:
                # I dont think this should happen
                r['dispersion']['netCDFs'] = netcdfs
            else:
                r['dispersion']['netCDF'] = netcdfs[0]

    KMZ_PATTERN = '*.kmz'
    IMAGE_PATTERN = '*.png'
    SMOKE_KMZ_MATCHER = re.compile('.*smoke.*kmz')
    FIRE_KMZ_MATCHER = re.compile('.*fire.*kmz')
    HOURLY_IMG_MATCHER = re.compile('.*/hourly_.*')
    THREE_HOUR_IMG_MATCHER = re.compile('.*/three_hour_.*')
    DAILY_AVG_IMG_MATCHER = re.compile('.*/daily_average_.*')
    DAILY_MAX_IMG_MATCHER = re.compile('.*/daily_maximum_.*')
    def _process_visualization(self, d, r):
        # TODO: look in 'd' to see the target of visualization, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        # Note:  glob.glob introduced recursive option in python 3.5. So,
        #  we just need to recursively walk the directory
        kmzs = set(self._find_files(d['output']['directory'], self.KMZ_PATTERN))
        smoke_kmz = fire_kmz = None
        for kmz in list(kmzs): # cast to list to allow discarding in loop
            if smoke_kmz and fire_kmz:
                break
            if not smoke_kmz and self.SMOKE_KMZ_MATCHER.match(kmz):
                smoke_kmz = kmz
                kmzs.discard(kmz)
                continue
            if not fire_kmz and self.FIRE_KMZ_MATCHER.match(kmz):
                fire_kmz = kmz
                kmzs.discard(kmz)
                continue
        r['visualization']['kmzs'] = {
            "smoke": smoke_kmz,
            "fire": fire_kmz
        }
        if kmzs:
            r['visualization']['kmzs']['other'] = list(kmzs)

        images = self._find_files(d['output']['directory'], self.IMAGE_PATTERN)
        hourly = [e for e in images if self.HOURLY_IMG_MATCHER.match(e)]
        three_hour = [e for e in images if self.THREE_HOUR_IMG_MATCHER.match(e)]
        daily_max = [e for e in images if self.DAILY_MAX_IMG_MATCHER.match(e)]
        daily_avg = [e for e in images if self.DAILY_AVG_IMG_MATCHER.match(e)]
        r['visualization']['images'] = {
            "hourly": hourly,
            "three_hour": three_hour,
            "daily": {
               "average": daily_avg,
               "maximum": daily_max
            },
            "other": list(set(images) - set(hourly) - set(three_hour)
                - set(daily_max) - set(daily_avg)),
        }

    def _find_files(self, directory, pattern):
        """Recursively walks directory looking for files whose name match pattern

        args
         - directory -- root directory to walk
         - pattern -- string filename pattern
        """
        matches = []
        for root, dirnames, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))
        return [m.replace(directory, '').lstrip('/') for m in matches]