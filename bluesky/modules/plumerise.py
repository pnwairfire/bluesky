"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__ = "Joel Dubowy"

import copy
import datetime
import logging
import os
import csv

from plumerise import sev, feps, __version__ as plumerise_version
from pyairfire import sun, osutils
import numpy

from bluesky import datautils, datetimeutils, locationutils
from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'run'
]

__version__ = "0.1.1"


def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    compute_func = ComputeFunction(fires_manager)

    working_dir = compute_func.config.get('working_dir')
    delete_if_no_error = compute_func.config.get('delete_working_dir_if_no_error')
    with osutils.create_working_dir(working_dir=working_dir,
            delete_if_no_error=delete_if_no_error) as working_dir:
        for fire in fires_manager.fires:
            with fires_manager.fire_failure_handler(fire):
                compute_func(fire, working_dir=working_dir)

    # Make sure to distribute the heat if it was loaded here.
    if compute_func.config.get("load_heat"):
        datautils.summarize_all_levels(fires_manager, 'heat')

    # TODO: spread out emissions over plume and set in activity or fuelbed
    #   objects ??? (be consistent with profiled emissions, setting in
    #   same place or not setting at all)

    # TODO: set summary?
    # fires_manager.summarize(plumerise=...)

INVALID_PLUMERISE_MODEL_MSG = "Invalid plumerise model: '{}'"
NO_ACTIVITY_ERROR_MSG = "Missing activity data required for plumerise"
MISSING_AREA_ERROR_MSG = "Missing fire activity area required for plumerise"
MISSING_CONSUMPTION_ERROR_MSG = "Missing fire activity consumption data required for FEPS plumerise"
MISSING_TIMEPROFILE_ERROR_MSG = "Missing timeprofile data required for computing FEPS plumerise"
MISSING_START_TIME_ERROR_MSG = "Missing fire activity start time required by FEPS plumerise"
MISSING_LOCALMET_ERROR_MSG = "Missing localmet data required for computing SEV plumerise"

class ComputeFunction(object):
    def __init__(self, fires_manager):
        model = Config().get('plumerise', 'model').lower()
        fires_manager.processed(__name__, __version__,
            plumerise_version=plumerise_version, model=model)

        logging.debug('Generating %s plumerise compution function', model)
        generator = getattr(self, '_{}'.format(model), None)
        if not generator:
            raise BlueSkyConfigurationError(
                INVALID_PLUMERISE_MODEL_MSG.format(model))

        self.config = Config().get('plumerise', model)
        self._compute_func = generator(self.config)

        if self.config.get('working_dir'):
            fires_manager.plumerise = {
                'output': {
                    'directory': self.config['working_dir']
                }
            }

    def __call__(self, fire, working_dir=None):
        if 'activity' not in fire:
            raise ValueError(NO_ACTIVITY_ERROR_MSG)

        # just calling fire.locations will trigger missing area
        # exception if any are missing area
        fire.locations

        self._compute_func(fire, working_dir)

    ## compute function generators

    def _feps(self, config):
        pr = feps.FEPSPlumeRise(**config)

        def _get_fire_working_dir(fire, working_dir):
            fire_working_dir = os.path.join(working_dir,
                "feps-plumerise-{}".format(fire.id))
            if not os.path.exists(fire_working_dir):
                os.makedirs(fire_working_dir)
            return fire_working_dir

        def _loadHeat(plume_dir):
            plumeFile = os.path.join(plume_dir, "plume.txt")

            heat = {"flaming": [0],
                    "residual": [0],
                    "smoldering": [0],
                    "total": [0]}

            #TODO: Investigate if this is the right kind of heat
            for row in csv.DictReader(open(plumeFile, 'r'), skipinitialspace=True):
                heat["total"][0] = heat["total"][0] + float(row["heat"])
                heat["flaming"][0] = heat["flaming"][0] + float(row["heat"])

            return heat

        def _f(fire, working_dir):
            # TODO: create and change to working directory here (per fire),
            #   above (one working dir per all fires), or below (per activity
            #   window)...or just let plumerise create temp workingdir (as
            #   it's currently doing?
            for aa in fire.active_areas:
                start = aa.get('start')
                if not start:
                    raise ValueError(MISSING_START_TIME_ERROR_MSG)
                start = datetimeutils.parse_datetime(aa.get('start'), 'start')

                if not aa.get('timeprofile'):
                    raise ValueError(MISSING_TIMEPROFILE_ERROR_MSG)

                for loc in aa.locations:
                    if not loc.get('consumption', {}).get('summary'):
                        raise ValueError(MISSING_CONSUMPTION_ERROR_MSG)

                    # Fill in missing sunrise / sunset
                    if any([loc.get(k) is None for k in
                            ('sunrise_hour', 'sunset_hour')]):

                        # default: UTC
                        utc_offset = datetimeutils.parse_utc_offset(
                            loc.get('utc_offset', 0.0))

                        # Use NOAA-standard sunrise/sunset calculations
                        latlng = locationutils.LatLng(loc)
                        s = sun.Sun(lat=latlng.latitude, lng=latlng.longitude)
                        d = start.date()
                        # just set them both, even if one is already set
                        loc["sunrise_hour"] = s.sunrise_hr(d, utc_offset)
                        loc["sunset_hour"] = s.sunset_hr(d, utc_offset)

                    fire_working_dir = _get_fire_working_dir(fire, working_dir)

                    met_info = FepsMetParams(loc.get('localmet')).dict

                    # TOOD: set "moisture_duff" from fuel moisture module
                    #   output, once it's implemented

                    # Note that we'll be passing in a dict set with the location
                    # information (plue met), not the location dict itself.
                    # so, loc will not be modified by the call to compute
                    # (It used to be augmented with default values for
                    # the met related inputs, which are now set from localmet data
                    # if avbailable)
                    loc_info = dict(loc, **met_info)

                    plumerise_data = pr.compute(aa['timeprofile'],
                        loc['consumption']['summary'], loc_info,
                        working_dir=fire_working_dir)
                    loc['plumerise'] = plumerise_data['hours']

                    if config.get("load_heat"):
                        if 'fuelbeds' not in loc:
                            raise ValueError(
                                "Fuelbeds should exist before loading heat in plumerise")
                        loc["fuelbeds"][0]["heat"] = _loadHeat(fire_working_dir)
                    # TODO: do anything with plumerise_data['heat'] ?
                    # SEE: Canadian additon to this system above

        return _f

    def _sev(self, config):
        pr = sev.SEVPlumeRise(**config)

        def _f(fire, working_dir):
            fire_frp = fire.get('meta', {}).get('frp')
            for aa in fire.active_areas:
                for loc in aa.locations:
                    if not loc.get('localmet'):
                        raise ValueError(MISSING_LOCALMET_ERROR_MSG)
                    # TODO: if fire_frp is defined but activity's frp isn't,
                    #   do we need to multiple by activity's
                    #   percentage of the fire's total area?
                    loc_frp = loc.get('frp', fire_frp)
                    plumerise_data = pr.compute(loc['localmet'],
                        loc['area'], frp=loc_frp)
                    loc['plumerise'] = plumerise_data['hours']

        return _f


class FepsMetParams(object):

    def __init__(self, localmet):
        self._localmet = localmet
        self._data = {}

        if self._localmet:
            try:
                self._set_max_min_wind()
                self._set_max_min_wind_aloft()
                self._set_max_min_humidity()
                self._set_max_min_temp()
                self._set_max_min_temp_hour()
                self._set_sunrise_hour()
                self._set_sunset_hour()

                # TODO: set "snow_month" if it's available in met data?
                # TODO: set "rain_days" if it's available in met data?
                # TODO: somehow compute 'moisture_duff' from localmet

            except Exception as e:
                logging.warning("Failed to set locamet data for plumerise: %s", e)
                raise

    @property
    def dict(self):
        return self._data

    def _set_max_min_wind(self):
        try:
            l2norm_vals = []
            for hr_vals in self._localmet.values():
                if hr_vals.get('U10M') is not None and hr_vals.get('V10M') is not None:
                    l2norm_vals.append(
                        numpy.linalg.norm([hr_vals['U10M'], hr_vals['V10M']])
                    )
            if l2norm_vals:
                self._data.update({
                    'min_wind_aloft': min(l2norm_vals),
                    'max_wind_aloft': max(l2norm_vals),
                })
        except Exception as e:
            logging.warning("Failed to set locamet data for plumerise: %s", e)

    def _set_max_min_wind_aloft(self):
        self._data.update(self._compute_min_max('WSPD', 'wind'))

    def _set_max_min_humidity(self):
        self._data.update(self._compute_min_max('RELH', 'humid'))

    def _set_max_min_temp(self):
        self._data.update(self._compute_min_max('TEMP', 'temp'))

    def _set_max_min_temp_hour(self):
        # TODO: set integer indices of hours with max and min temps?
        pass

    def _set_sunrise_hour(self):
        self._set_any_val('sunrise_hour')

    def _set_sunset_hour(self):
        self._set_any_val('sunset_hour')

    def _compute_min_max(self, met_field, key_suffix):
        try:
            all_vals = [val for hr in self._localmet.values() for val in hr.get(met_field, [])]
            all_vals = [val for val in all_vals if val is not None]

            if all_vals:
                return {
                    'max_' + key_suffix: max(all_vals),
                    'min_' + key_suffix: min(all_vals)
                }
        except Exception as e:
            logging.warning("Failed to compute min/max of %s: %s", met_field, e)

        return {}

    def _set_any_val(self, met_field, plumerise_field=None):
        for hr_vals in self._localmet.values():
            if hr_vals.get(met_field) is not None:
                self._data[plumerise_field or met_field] = hr_vals[met_field]
