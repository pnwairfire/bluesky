"""bluesky.exporters"""

__author__ = "Joel Dubowy"

import fnmatch
import glob
import json
import logging
import os
import re
import shutil
import tempfile
from io import StringIO, BytesIO

from bluesky import io
from bluesky.config import Config

# TODO: Support exporting VSMOKE dispersion, which would include KMLs
#   and not have separate visualization section


class ExporterBase(object):

    def __init__(self, extra_exports):
        self._export_mode = self.__class__.__module__.split('.')[-1]

        self._extra_exports = extra_exports
        self._handle_existing = self.config('handle_existing')

    def config(self, *keys):
        return Config().get('export', self._export_mode, *keys)

    def export(self, fires_manager):
        raise NotImplementedError("Bluesky's {} exporter needs to "
            "implement method 'export'".format(self.__class__.__name__))

    def _get_output_dump(self, fires_manager, compress=False):
        d = BytesIO() if compress else StringIO()
        fires_manager.dumps(output_stream=d, compress=compress)
        return d.getvalue()

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

        json_output_filename = self.config('json_output_filename')
        r['output_json'] = json_output_filename

        fires_manager.export = fires_manager.export or {}
        fires_manager.export[self.EXPORT_KEY] = r
        with open(os.path.join(output_dir, json_output_filename), 'w') as f:
            fires_manager.dumps(output_stream=f)

        if create_tarball:
            return io.create_tarball(output_dir,
                tarball_pathname=self._get_tarball_pathname(dest))

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

        output_dir = io.create_dir_or_handle_existing(
            os.path.join(dest, self._output_dir_name),
            handle_existing=self._handle_existing)

        return output_dir


    def _gather_bundle(self, fires_manager, output_dir):
        extra_exports_dir_name = self.config('extra_exports_dir_name')
        if extra_exports_dir_name:
            extra_exports_path_name = os.path.join(output_dir,
                extra_exports_dir_name)
            if not os.path.exists(extra_exports_path_name):
                os.makedirs(extra_exports_path_name)
        r = {}
        dirs_to_copy = {}
        for k in self._extra_exports:
            module_info = getattr(fires_manager, k)
            if module_info and module_info.get('output', {}):
                directories = module_info["output"].get("directories", [])
                if module_info["output"].get('directory'):
                    directories.append(module_info["output"]['directory'])
                for d in [d.rstrip('/') for d in directories]:
                    dirs_to_copy[d] = dirs_to_copy.get(d, [])
                    dirs_to_copy[d].append(k)

        for directory, extra_exports in list(dirs_to_copy.items()):
            # TODO: See comment in bluesky.io.create_dir_or_handle_existing
            #   about getting shutil.copytree to work in the case
            #   where self._handle_existing=='write_in_place'
            if extra_exports_dir_name:
                new_dirname = extra_exports_dir_name
                for f in glob.glob(os.path.join(directory, '*')):
                    if os.path.isdir(f):
                        shutil.copytree(f, os.path.join(
                            extra_exports_path_name, os.path.basename(f)))
                    else:
                        shutil.copy(f, extra_exports_path_name)
                # TODO: use something other than shutil.copytree,
                #   which fails when dir already exists
            else:
                new_dirname = '-'.join(extra_exports)
                shutil.copytree(directory, os.path.join(output_dir, new_dirname))
            for k in extra_exports:
                r[k] = {'sub_directory': new_dirname}
                processor = getattr(self, '_process_{}'.format(k), None)
                if processor:
                    processor(getattr(fires_manager, k), r)

        return r


    ##
    ## Extra export - Dispersion
    ##

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


    ##
    ## Extra export - Visualization
    ##

    IMAGE_PATTERN = '*.png'
    SERIES_IMG_MATCHER = re.compile('.*_\d+.png')
    LEGEND_IMG_MATCHER = re.compile('.*colorbar.*\.png')

    def _process_images(self, directory):
        """Produces new image results json structure

        Note: This method uses recursion in order to handle variable
        image nesting depth. (e.g. The daily max and avg image sets have
        extra nesting due to possibly multiple UTC offsets.)
        """
        images = {}
        def _set(remaining_path, *path_elements):
            # Don't include saved, pre-reprojected images
            # (REPROJECT_IMAGES_SAVE_ORIGINAL=True)
            if remaining_path.find('saved-original-images/') >= 0:
                return

            if remaining_path:
                parent_path, directory = os.path.split(remaining_path)
                _set(parent_path, *(list(path_elements) + [directory]))
            else:
                image_name = path_elements[0]
                directory = os.path.join(*list(reversed(path_elements[1:])))
                color_scheme_dict = images
                for e in reversed(path_elements[1:-1]):
                    color_scheme_dict[e] = color_scheme_dict.get(e, {})
                    color_scheme_dict = color_scheme_dict[e]
                if color_scheme_dict == {}:
                    color_scheme_dict.update({
                        "directory": directory,
                        "legend": None,
                        "series": [],
                        "other_images": []
                    })
                if color_scheme_dict['directory'] != directory:
                    # TODO: somehow handle this; e.g. we could have 'images'
                    #   reference an array of image directory group objects, and
                    #   add 'time_series' and 'color_scheme' keys to each object
                    #   (though these extra keys wouldn't really be necessary
                    #   since their values can be extracted from the directory)
                    raise RuntimeError("Multiple image directories with the same "
                        "time series and color scheme identifiers - {} vs. {}".format(
                        color_scheme_dict['directory'], directory))

                if self.SERIES_IMG_MATCHER.match(image_name):
                    color_scheme_dict['series'].append(image_name)
                elif (color_scheme_dict['legend'] is None and
                        self.LEGEND_IMG_MATCHER.match(image_name)):
                    color_scheme_dict['legend'] = image_name
                else:
                    color_scheme_dict['other_images'].append(image_name)


        for i in self._find_files(directory, self.IMAGE_PATTERN):
            _set(i)

        return images

    def _sort_images(self, images):
        """Sorts any 'series' and 'other_images' in images dict.

        Note: See note in _process_images regarding recursion and variable
        image nesting depth.
        """
        if 'series' in images:
            images['series'].sort()
            images['other_images'].sort()
        else:
            for v in images.values():
                self._sort_images(v)

    JSON_PATTERN = '*.json'
    KMZ_PATTERN = '*.kmz'
    KML_PATTERN = '*.kml'
    CSV_PATTERN = '*.csv'
    NETCDF_PATTERN = '*.nc'
    # TODO: compile regexes from file name config settings, since the following
    #   patterns may be invalid if user specifies custom names
    TRAJ_KML_PATTERN = re.compile('.*traj.*kml')
    SMOKE_KMZ_MATCHER = re.compile('.*smoke.*kmz')
    FIRE_KMZ_MATCHER = re.compile('.*fire.*kmz')
    FIRE_LOCATIONS_CSV_MATCHER = re.compile('.*/fire_locations.*')
    FIRE_EVENTS_CSV_MATCHER = re.compile('.*/fire_events.*')
    FIRE_EMISSIONS_CSV_MATCHER = re.compile('.*/fire_emissions.*')

    def _process_visualization(self, d, r):
        for target_info in d.get('targets', []):
            directory = target_info.get('output', {}).get('directory')
            if directory:
                f = "_process_{}_visualization".format(target_info['target'])
                target_processor = getattr(self, f, None)
                if target_processor:
                    r['visualization'][target_info['target']] = {}
                    target_processor(directory, r)

    def _process_trajectories_visualization(self, directory, r):
        kmls = self._find_files(directory, self.KML_PATTERN)
        r['visualization']['trajectories']['kmls'] = self._pick_out_files(kmls,
            trajectories=self.TRAJ_KML_PATTERN)

    def _process_dispersion_visualization(self, directory, r):
        # TODO: look in 'd' to see the target of visualization, what files
        #   exist, etc.; it won't necessarily say - so that's why we need
        #   the back-up logic of looking for specific files
        kmzs = self._find_files(directory, self.KMZ_PATTERN)
        r['visualization']['dispersion']['kmzs'] = self._pick_out_files(kmzs,
            smoke=self.SMOKE_KMZ_MATCHER, fire=self.FIRE_KMZ_MATCHER)

        r['visualization']['dispersion']['images'] = self._process_images(directory)
        self._sort_images(r['visualization']['dispersion']['images'])

        csvs = self._find_files(directory, self.CSV_PATTERN)
        r['visualization']['dispersion']['csvs'] = self._pick_out_files(csvs,
            fire_locations=self.FIRE_LOCATIONS_CSV_MATCHER,
            fire_events=self.FIRE_EVENTS_CSV_MATCHER,
            fire_emissions=self.FIRE_EMISSIONS_CSV_MATCHER)


    ##
    ## Extra Exports - Output
    ##

    # Note: we don't need any extra code to process 'output' module output


    ##
    ## General helpers
    ##

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

    def _get_tarball_pathname(self, dest):
        tarball_name = self.config('tarball_name')
        if tarball_name:
            os.path.join(dest, tarball_name)
        # else, returns None
