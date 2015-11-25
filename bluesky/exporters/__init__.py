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

        r = {}

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

        # TODO: support options to dump fire and emissions information to csv
        #   (i.e. fire_locations.csv, fire_events.csv, and fire_emissions.csv)

        if not create_tarball:
            r['directory'] = output_dir

        json_output_filename = self.config('json_output_filename') or 'output.json'
        r['output_json'] = json_output_filename

        fires_manager.export = fires_manager.export or {}
        fires_manager.export[self.EXPORT_KEY] = r
        with open(os.path.join(output_dir, json_output_filename), 'w') as f:
            fires_manager.dumps(output_stream=f)

        if create_tarball:
            tarball_name = self.config('tarball_name')
            tarball = (os.path.join(dest, tarball_name) if tarball_name
                else "{}.tar.gz".format(output_dir))
            if os.path.exists(tarball):
                os.remove(tarball)
            with tarfile.open(tarball, "w:gz") as tar:
                tar.add(output_dir, arcname=os.path.basename(output_dir))
            return tarball

        return output_dir

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
                r['dispersion']['netcdfs'] = netcdfs
            else:
                r['dispersion']['netcdf'] = netcdfs[0]

        # TODO: list other hysplit output files; maybe make this configurable

    KMZ_PATTERN = '*.kmz'
    IMAGE_PATTERN = '*.png'
    CSV_PATTERN = '*.csv'
    SMOKE_KMZ_MATCHER = re.compile('.*smoke.*kmz')
    FIRE_KMZ_MATCHER = re.compile('.*fire.*kmz')
    HOURLY_IMG_MATCHER = re.compile('.*/hourly_.*')
    THREE_HOUR_IMG_MATCHER = re.compile('.*/three_hour_.*')
    DAILY_AVG_IMG_MATCHER = re.compile('.*/daily_average_.*')
    DAILY_MAX_IMG_MATCHER = re.compile('.*/daily_maximum_.*')
    FIRE_LOCATIONS_CSV_MATCHER = re.compile('.*/fire_locations.*')
    FIRE_EVENTS_CSV_MATCHER = re.compile('.*/fire_events.*')
    FIRE_EMISSIONS_CSV_MATCHER = re.compile('.*/fire_emissions.*')
    def _process_visualization(self, d, r):
        # TODO: look in 'd' to see the target of visualization, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        kmzs = self._find_files(d['output']['directory'], self.KMZ_PATTERN)
        r['visualization']['kmzs'] = self._pick_out_files(kmzs,
            smoke=self.SMOKE_KMZ_MATCHER, fire=self.FIRE_KMZ_MATCHER)

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

        csvs = self._find_files(d['output']['directory'], self.CSV_PATTERN)
        r['visualization']['csvs'] = self._pick_out_files(csvs,
            fire_locations=self.FIRE_LOCATIONS_CSV_MATCHER,
            fire_events=self.FIRE_EVENTS_CSV_MATCHER,
            fire_emissions=self.FIRE_EMISSIONS_CSV_MATCHER)

    def _pick_out_files(self, found_files, **patterns):
        found_files = set(found_files)
        selected = {}
        smoke_kmz = fire_kmz = None
        for f in list(found_files): # cast to list to allow discarding in loop
            if not any([not selected.get(p) for p in patterns]):
                break
            for p in patterns:
                if not selected.get(p) and patterns[p].match(f):
                    selected[p] = f
                    found_files.discard(f)
                    break

        if found_files:
            selected['other'] = list(found_files)

        return selected



    def _find_files(self, directory, pattern):
        """Recursively walks directory looking for files whose name match pattern

        args
         - directory -- root directory to walk
         - pattern -- string filename pattern

        Note:  glob.glob introduced recursive option in python 3.5. So,
         we need to recursively walk the directory with os.walk
        """
        matches = []
        for root, dirnames, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))
        return [m.replace(directory, '').lstrip('/') for m in matches]