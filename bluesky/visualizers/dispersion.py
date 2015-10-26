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

DEFAULT_FILE_NAMES = {
    "fire_locations_csv": 'fire_locations.csv',
    "fire_events_csv": 'fire_events.csv',
    "smoke_dispersion_kmz": 'smoke_dispersion.kmz',
    "fire_kmz": 'fire_information.kmz'
}

def pick_representative_fuelbed(fire):
    sorted_fuelbeds = reversed(fire.get('fuelbeds', []), key=lambda fb: fb['pct'])
    if sorted_fuelbeds:
        return sorted_fuelbeds[0]['fccs_id']

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

        files = {
            'fire_locations_csv': self._get_file_name('fire_locations_csv'),
            'fire_events_csv': self._get_file_name('fire_events_csv'),
            'smoke_dispersion_kmz': self._get_file_name('smoke_dispersion_kmz'),
            'fire_kmz': self._get_file_name('fire_kmz')
        }

        self._generate_fire_csv_files(files['fire_locations_csv']['pathname'],
            files['fire_events_csv']['pathname'])

        args = BlueskyKmlArgs(
            output_directory=output_directory,
            configfile=None, # TODO: allow this to be configurable?
            prettykml=self._config.get('prettykml'),
            verbose=False, # TODO: set to True if logging level is DEBUG
            config_options={}, # TODO: set anything here?
            inputfile=hysplit_output_file,
            fire_locations_csv=files['fire_locations_csv']['pathname'],
            fire_events_csv=files['fire_events_csv']['pathname'],
            smoke_dispersion_kmz_file=files['smoke_dispersion_kmz']['pathname'],
            fire_kmz_file=files['fire_kmz']['pathname'],
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
                "smoke_dispersion_kmz_filename": files['smoke_dispersion_kmz']['name'],
                "fire_kmz_filename": files['fire_kmz']['name'],
                "fire_locations_csv_filename": files['fire_locations_csv']['name'],
                "fire_events_csv_filename": files['fire_events_csv']['name']
                # TODO: add location of image files, etc.
            }
        }

    def _get_file_name(f):
        name = self_config.get('{}_filename'.format(f), DEFAULT_FILENAMES[f])
        return {
            "name": name,
            "pathname": os.path.join(output_directory, name)
        }


    FIRE_LOCATIONS_CSV_FIELDS = [
        ('id', lambda f: f.id),
        ('fccs_number', pick_representative_fuelbed)
    ]
    """List of fire location csv fields, with function to extract from fire object"""

    FIRE_EVENTS_CSV_FIELDS = [
        ('name', _assign_event_name),
        ('total_area', _update_event_area),
        ('total_pm25', _update_total_emissions_species('pm25')),
        ('total_pm10', _update_total_emissions_species('pm10')),
        ('total_co', _update_total_emissions_species('co')),
        ('total_co2', _update_total_emissions_species('co2')),
        ('total_ch4', _update_total_emissions_species('ch4')),
        ('total_nmhc', _update_total_emissions_species('nmhc')),
        ('total_nox', _update_total_emissions_species('nox')),
        ('total_nh3', _update_total_emissions_species('nh3')),
        ('total_so2', _update_total_emissions_species('so2')),
        ('total_voc', _update_total_emissions_species('voc'))
    ]
    """List of fire event csv fields, with function to extract from fire object
    and aggregate.  Note that this list lacks 'id', which is the first column.
    """

    def _collect_csv_fields(self):
        # As we iterate through fires, collecting necessary fields, collect
        # events information as well
        fires = {}
        events = {}
        for fire in self._fires:
            fires.append({k: l(fire) or '' for k, l in self.FIRE_LOCATIONS_CSV_FIELDS})
            event_id = fire.get('event_of', {}).get('id')
            if event_id:
                events[event_id] = events.get(event_id, {})
                for k, l in self.FIRE_EVENTS_CSV_FIELDS:
                    events[event_id][k] = l(events[event_id], f)
        return fires, events

    def _generate_fire_csv_file(self, fire_locations_csv_pathname,
            fire_events_csv_pathname):
        """Generates fire locations and events csvs

        These are used by blueskykml, but are also used by end users.
        If it weren't for end users wanting the files, we might want to
        consider refactoring blueskykml to accept the fire data in
        memory (in the call to makedispersionkml.main(args)) rather
        reading it from file.
        """
        # TODO: Make sure that the files don't already exists
        # TODO: look in blueskykml code to see what it uses from the two csvs

        fires, events = self._collect_csv_fields()
        with open(fire_locations_csv_pathname, 'w') as f:
            f.write(','.join([k for k, l in self.FIRE_LOCATIONS_CSV_FIELDS]))
            for fire in fires:
                f.write(','.join([fire[k] for k, l in self.FIRE_LOCATIONS_CSV_FIELDS]))

        with open(fire_events_csv_pathname, 'w') as f:
            f.write(','.join([k for k, l in self.FIRE_EVENTS_CSV_FIELDS]))
            for e_id, event in events.items():
                f.write(','.join([e_id] +
                    [event[k] for k, l in self.FIRE_EVENTS_CSV_FIELDS]))

def _assign_event_name(event, fire):
    if fire['event_of']['name']:
        if event['name'] and fire['event_of']['name'] != event['name']:
            logging.warn("Fire {} event name conflict: '{}' != '{}'".format(
                fire['event_of']['name'], event['name']))
        event['name'] = fire['event_of']['name']

def _update_event_area(event, fire):
    if not fire.get('location', {}).get('area'):
        raise ValueError("Fire {} lacks area".format(fire.get('id')))
    event['total_area'] = event.get('total_area', 0.0) + fire

def _update_total_emissions_species(species):
    key = 'total_{}'.format(species)
    def f(event, fire):
        if key in event and event[key] is None:
            # previous fire didn't have this emissions value defined; abort so
            # that we don't end up with misleading partial total
            return

        # value will be set to non-None if species is defined for all fuelbeds
        event[key] = None
        if fire.get('fuelbeds'):
            values = [
                fb.get('emissions', {}).get('total', {}).get(species.upper())
                    for db in fire['fuelbeds']
            ]
            if not any([v is None for v in values]):
                event[key] = sum(values)
    return f