"""bluesky.exporters"""

__author__ = "Joel Dubowy"

import fnmatch
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile

from pyairfire import configuration


# TODO: Support exporting VSMOKE dispersion, which would include KMLs
#   and not have separate visualization section


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
        output_dir = self._create_output_dir(fires_manager, dest)
        r = self._gather_bundle(fires_manager, output_dir)

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
            self._create_tarball(dest, output_dir)

        return output_dir

    OUTPUT_DIR_NAME_WILDCARDS = [
        (re.compile('{dispersion_output_dir_name}'),
            lambda fires_manager: os.path.basename(fires_manager.dispersion and
                fires_manager.dispersion.get('output', {}).get('directory') or ''))
        # TDOO: any other?
    ]
    def _replace_output_dir_wild_cards(self, fires_manager, output_dir_name):
        if output_dir_name:
            for m, f in self.OUTPUT_DIR_NAME_WILDCARDS:
                try:
                    if m.search(output_dir_name):
                        output_dir_name = output_dir_name.replace(
                            m.pattern, f(fires_manager))
                except Exception as e:
                    logging.error("Failed to replace {} in export output dir "
                        "name - {}".format(m.pattern, str(e)))
                    # Just skip

        return output_dir_name

    def _create_output_dir(self, fires_manager, dest):
        self._output_dir_name = self._replace_output_dir_wild_cards(
            fires_manager, self.config('output_dir_name')) or fires_manager.run_id

        # create destination dir (to contain output dir) if necessary
        if not os.path.exists(dest):
            os.makedirs(dest)

        # if output dir exists, delete it or raise exception if not configured
        # to allow overwriting
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

        return output_dir

    def _gather_bundle(self, fires_manager, output_dir):
        r = {}

        dirs_to_copy = {}
        for k in self._extra_exports:
            d = getattr(fires_manager, k)
            if d and d.get('output', {}).get('directory'):
                dirs_to_copy[d['output']['directory']] = dirs_to_copy.get(
                    d['output']['directory'], [])
                dirs_to_copy[d['output']['directory']].append(k)
        for directory, extra_imports in list(dirs_to_copy.items()):
            new_dirname = '-'.join(extra_imports)
            shutil.copytree(directory, os.path.join(output_dir, new_dirname))
            for k in extra_imports:
                r[k] = {'sub_directory': new_dirname}
                processor = getattr(self, '_process_{}'.format(k), None)
                if processor:
                    processor(getattr(fires_manager, k), r)
        return r

    def _process_dispersion(self, d, r):
        # TODO: look in 'd' to see what model of dispersion was run, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        # TODO: Support option to rename nc file; other files too?
        r['dispersion'].update(self._find_netcdfs(d))

        # call sub methhods for model-specific logic
        if 'model' in d:
            model_processor = getattr(self, '_process_{}'.format(d['model']), None)
            if model_processor:
                model_processor(d, r)

    def _process_hysplit(self, d, r):
        # TODO: list other hysplit output files; maybe make this configurable
        pass

    def _process_vsmoke(self, d, r):
        # vsmoke produces KMZs
        # TODO: list kmzs under 'dispersion'?
        kmzs = self._find_files(d['output']['directory'], self.KMZ_PATTERN)
        r['dispersion']['kmzs'] = self._pick_out_files(kmzs,
            smoke=self.SMOKE_KMZ_MATCHER)
        json_files = self._find_files(d['output']['directory'],
            self.JSON_PATTERN)
        if json_files:
            r['dispersion']['json'] = json_files

    def _find_netcdfs(self, d):
        netcdfs = self._find_files(d['output']['directory'],
            self.NETCDF_PATTERN)
        if netcdfs:
            if len(netcdfs) > 1:
                # I dont think this should happen
                return {'netcdfs': netcdfs}
            else:
                return {'netcdf': netcdfs[0]}
        return {}


    IMAGE_PATTERN = '*.png'

    ## ******************** TO DELETE - BEGIN

    HOURLY_IMG_MATCHER = re.compile('.*/hourly_.*')
    THREE_HOUR_IMG_MATCHER = re.compile('.*/three_hour_.*')
    DAILY_AVG_IMG_MATCHER = re.compile('.*/daily_average_.*')
    DAILY_MAX_IMG_MATCHER = re.compile('.*/daily_maximum_.*')

    def _process_images_v1(self, d):
        """Produces original image results json structure

        TODO: delete once v2 has been adopted.
        """
        images = self._find_files(d['output']['directory'], self.IMAGE_PATTERN)
        hourly = [e for e in images if self.HOURLY_IMG_MATCHER.match(e)]
        three_hour = [e for e in images if self.THREE_HOUR_IMG_MATCHER.match(e)]
        daily_max = [e for e in images if self.DAILY_MAX_IMG_MATCHER.match(e)]
        daily_avg = [e for e in images if self.DAILY_AVG_IMG_MATCHER.match(e)]
        return {
            "hourly": hourly,
            "three_hour": three_hour,
            "daily": {
               "average": daily_avg,
               "maximum": daily_max
            },
            "other": list(set(images) - set(hourly) - set(three_hour)
                - set(daily_max) - set(daily_avg)),
        }

    ## ******************** TO DELETE - END

    SERIES_IMG_MATCHER = re.compile('.*_\d+.png')
    LEGEND_IMG_MATCHER = re.compile('.*colorbar_.*.png')

    def _process_images_v2(self, d):
        """Produces new image results json structure

        TODO: update README and other examples with new structure
        """
        images = {}
        for i in self._find_files(d['output']['directory'], self.IMAGE_PATTERN):
            directory, image_name = os.path.split(i)
            _, color_scheme = os.path.split(directory)
            _, time_series = os.path.split(_)
            images[time_series] = images.get(time_series, {})
            images[time_series][color_scheme] = images[time_series].get(
                color_scheme, {"directory": directory, "legend": None,
                "series": [], "other_images": []})
            if images[time_series][color_scheme]['directory'] != directory:
                # TODO: somehow handle this; e.g. we could have 'images'
                #   reference an array of image directory group objects, and
                #   add 'time_series' and 'color_scheme' keys to each object
                #   (though these extra keys wouldn't really be necessary
                #   since their values can be extracted from the directory)
                raise RuntimeError("Multiple image directories with the same "
                    "time series and color scheme identifiers - {} vs. {}".format(
                    images[time_series][color_scheme]['directory'], directory))

            if self.SERIES_IMG_MATCHER.match(image_name):
                images[time_series][color_scheme]['series'].append(image_name)
            elif (images[time_series][color_scheme]['legend'] is None and
                    self.LEGEND_IMG_MATCHER.match(image_name)):
                images[time_series][color_scheme]['legend'] = image_name
            else:
                images[time_series][color_scheme]['other_images'].append(image_name)
        images[time_series][color_scheme]['series'].sort()
        images[time_series][color_scheme]['other_images'].sort()
        return images

    JSON_PATTERN = '*.json'
    KMZ_PATTERN = '*.kmz'
    CSV_PATTERN = '*.csv'
    NETCDF_PATTERN = '*.nc'
    SMOKE_KMZ_MATCHER = re.compile('.*smoke.*kmz')
    FIRE_KMZ_MATCHER = re.compile('.*fire.*kmz')
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

        # TODO: remove v1 once v2 has been adopted, and replace the following
        #   code with:
        #     r['visualization']['images'] = self._process_images(d)
        img_ver = self.config('image_results_version') or 'v1'
        _f = getattr(self, '_process_images_{}'.format(img_ver), None)
        if not _f:
            raise RuntimeError("Invalid image_results_version: {}".format(img_ver))
        r['visualization']['images'] = _f(d)


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

    def _create_tarball(self, dest, output_dir):
        tarball_name = self.config('tarball_name')
        tarball = (os.path.join(dest, tarball_name) if tarball_name
            else "{}.tar.gz".format(output_dir))
        if os.path.exists(tarball):
            os.remove(tarball)
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(output_dir, arcname=os.path.basename(output_dir))
        return tarball
