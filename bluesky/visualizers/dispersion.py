"""bluesky.visualizers.disersion"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"


__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'HysplitVisualizer'
]
__version__ = "0.1.0"

import logging
import os
import uuid
from collections import namedtuple

from blueskykml import (
    makedispersionkml, makeaquiptdispersionkml, configuration,
    __version__ as blueskykml_version
)

from bluesky.exceptions import BlueSkyConfigurationError

ARGS = [
    "output_directory", "configfile",
    "prettykml", "verbose", "config_options",
    "inputfile","fire_locations_csv",
    "fire_events_csv", "smoke_dispersion_kmz_file",
    "fire_kmz_file","layer"
]
BlueskyKmlArgs = namedtuple('BlueskyKmlArgs', ARGS)

DEFAULT_SMOKE_DISPERSION_KMZ_FILENAME = 'smoke_dispersion.kmz'
DEFAULT_FIRE_KMZ_FILENAME = 'fire_information.kmz'
DEFAULT_FIRE_LOCATIONS_CSV_FILENAME = 'fire_locations.csv'
DEFAULT_FIRE_EVENTS_CSV_FILENAME = 'fire_events.csv'

class HysplitVisualizer(object):
    def __init__(self, hysplit_output_info, fires, **config):
        self._hysplit_output_info = hysplit_output_info
        self._fires = fires
        self._config = config

    def run(self):
        hysplit_output_directory = hysplit_output_info.get('directory')
        if not hysplit_output_directory:
            raise ValueError("hysplit output directory must be defined")
        if not os.path.isdir(hysplit_output_directory):
            raise RuntimeError("hysplit output directory {} is not valid".format(
                hysplit_output_directory))

        hysplit_output_file = hysplit_output_info.get('grid_filename')
        if not directory:
            raise ValueError("hysplit output file must be defined")
        hysplit_output_file = os.path.join(hysplit_output_directory, hysplit_output_file)
        if not os.path.isfile(hysplit_output_file):
            raise RuntimeError("hysplit output file {} does not exist".format(
                hysplit_output_file))

        run_id = hysplit_output_info.get('run_id') or uuid.uuid3()
        output_directory = self_config.get('output_dir') or hysplit_output_directory

        smoke_dispersion_kmz_filename = self_config.get(
            'smoke_dispersion_kmz_filename',
            DEFAULT_SMOKE_DISPERSION_KMZ_FILENAME)
        smoke_dispersion_kmz_file = os.path.join(output_directory,
            smoke_dispersion_kmz_filename)

        fire_kmz_filename = self_config.get(
            'fire_kmz_filename',
            DEFAULT_FIRE_KMZ_FILENAME)
        fire_kmz_file = os.path.join(output_directory, fire_kmz_filename)

        fire_locations_csv_filename = self_config.get(
            'fire_locations_csv_filename',
            DEFAULT_FIRE_LOCATIONS_CSV_FILENAME)
        fire_locations_csv_file = os.path.join(output_directory,
            fire_locations_csv_filename)

        fire_events_csv_filename = self_config.get(
            'fire_events_csv_filename',
            DEFAULT_FIRE_EVENTS_CSV_FILENAME)
        fire_events_csv_file = os.path.join(output_directory,
            fire_events_csv_filename)
        # TODO: generate fires locations csv, or refactor blueskykml to accept
        #  fires as json? (look in blueskykml code to see what it uses from the csv)
        # TODO: generate fire events csv ? (look in blueskykml code to see
        #  what it uses from the csv)

        args = BlueskyKmlArgs(
            output_directory=output_directory,
            configfile=None, # TODO: allow this to be configurable?
            prettykml=self._config.get('prettykml'),
            verbose=False, # TODO: set to True if logging level is DEBUG
            config_options={}, # TODO: set anything here?
            inputfile=hysplit_output_file,
            fire_locations_csv=fire_locations_csv_file,
            fire_events_csv=fire_events_csv_file,
            smoke_dispersion_kmz_file=smoke_dispersion_kmz_file,
            fire_kmz_file=fire_kmz_file,
            # even though 'layer' is an integer index, the option must be of type
            # string or else config.get(section, "LAYER") will fail with error:
            #  > TypeError: argument of type 'int' is not iterable
            # it will be cast to int if specified
            layer=str(self._config.get('layer'))
        )


        try:
            # TODO: clean up any outputs created?  Should this be toggleable
            #   via config setting
            if self._config.get('is_aquipt'):
                makeaquiptdispersionkml.main(args)
            else:
                makedispersionkml.main(args)
        except configuration.ConfigurationError, e:
            raise BlueSkyConfigurationError(".....")

        return {
            'blueskykml_version': blueskykml_version
            "output": {
                "run_id": run_guid,
                "directory": output_directory,
                "hysplit_output_file": hysplit_output_file,
                "smoke_dispersion_kmz_filename": smoke_dispersion_kmz_filename,
                "fire_kmz_filename": fire_kmz_filename,
                "fire_locations_csv_filename": fire_locations_csv_filename,
                "fire_events_csv_filename": fire_events_csv_filename,
                # TODO: add location of image files, etc.
        }
