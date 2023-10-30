import logging
import math
import copy

from afdatetime.parsing import parse_datetime
from pyairfire.data.utils import multiply_nested_data

from bluesky.models.fires import Fire
from bluesky.exceptions import BlueSkyConfigurationError
from .. import GRAMS_PER_TON
from .emissions_file_utils import get_emissions_rows_data

__all__ = [
    'EmissionsSplitter'
]


# use a delta theta of 15 degrees (convert to radians) and a radius of 0.0005
RADIANS_PER_DEGREE   = 0.01745329251994329576
DTHETA = 15.0 * RADIANS_PER_DEGREE
DR =     0.0005

class EmissionsSplitter():
    def __init__(self, config_getter, reduction_factor, grid_params,
            num_traunches, fires):
        self._config_getter = config_getter
        self._reduction_factor = reduction_factor
        self._grid_params = grid_params
        self._num_traunches = num_traunches
        self._fires = fires

        self._set_dx_dy()
        self._set_deltsec()
        self._set_numpar_per_src_per_timestep()
        self._set_target_mass()
        self._set_emissions_rate_target()

    ##
    ## Setup
    ##

    def _set_dx_dy(self):
        # center lng of domain
        center_lng = self._grid_params['center_longitude']

        # grid cell sizes
        d_lat = self._grid_params['spacing_latitude']
        d_lng = self._grid_params['spacing_longitude']

        # dx and dy from lat lon info (meters)
        self._dx = 111.0 * d_lng * abs( math.cos(RADIANS_PER_DEGREE*center_lng) ) * 1000.0
        self._dy = 111.0 * d_lat * 1000.0

    def _set_deltsec(self):
        # DELT can be zero; set to 1 if so
        delt = self._config_getter('DELT') or 1
        self._deltsec = abs(delt/60.0)

    def _set_numpar_per_src_per_timestep(self):
        # NUMPAR allocated per fires source
        num_traunches = max(1, self._config_getter('NPROCESSES'))
        # Handle case of no fires - set num_fires_per_traunche to 1
        num_fires_per_traunche = len(self._fires)/num_traunches or 1
        # number of particles per source per hour
        numpar = abs(int(self._config_getter('NUMPAR')))
        numpar_per_src = float(math.ceil(numpar/num_fires_per_traunche))
        if ( numpar_per_src < 1.0 ):
          numpar_per_src = 1.0

        # number of particles per source per time step
        numpar_per_src_per_timestep = math.ceil(numpar_per_src*self._deltsec)
        self._numpar_per_src_per_timestep = max(1.0, numpar_per_src_per_timestep)

    def _set_target_mass(self):
        # TODO: set DZ from fires data?
        DZ = 500.0  # in meters

        # target PM2.5 value (ug/m3)
        target_pm25  = self._config_getter('emissions_split', 'target_pm25') # i.e. PM25star
        min_pm25 = self._config_getter('emissions_split', 'min_pm25')
        if min_pm25 and target_pm25 <= min_pm25:
            raise BlueSkyConfigurationError("Target PM2.5 must be greater than "
                "min PM2.5 in HYSPLIT emissions splitting code")

        # target mass per particle (grams)
        self._target_mass = target_pm25 * self._dx * self._dy * DZ / 1e6
        self._min_mass = min_pm25 and (min_pm25 * self._dx * self._dy * DZ / 1e6)

    def _set_emissions_rate_target(self):
        # for each hour, if emissions exceed threshold, split emissions out
        # amongst minumum number of sublocations necessary to get per-location
        # emissions below threshold; if not all are needed, set those extra
        # locations to zero (some hours will require no re-allocation at all)

        # emission rate target
        self._emissions_rate_target = (
            self._target_mass * self._numpar_per_src_per_timestep / self._deltsec)
        self._emissions_rate_min = self._min_mass and (
            self._min_mass * self._numpar_per_src_per_timestep / self._deltsec)

    ##
    ## Public API
    ##

    def split(self):
        if not self._config_getter('emissions_split', 'enabled'):
            return self._fires

        fires = []

        for fire in self._fires:
            try:
                max_emiss_rate = self._compute_max_emission_rate(fire)
                logging.debug("Max emissions rate for fire centered at lat, lon %f, %f: (%f)",
                    fire.latitude, fire.longitude, max_emiss_rate)

                if self._emissions_rate_min and max_emiss_rate < self._emissions_rate_min:
                    logging.info("Removing fire centered at lat, lon %f, %f for low pm25 rate (%f)",
                        fire.latitude, fire.longitude, max_emiss_rate)
                    continue

                # number of times to split the input rate
                num_split = max(1, math.ceil(max_emiss_rate / self._emissions_rate_target))

                if num_split == 1:
                    fires.append(fire)

                else:
                    lat_lngs = self._compute_new_lat_lngs(fire, num_split)
                    split_fires = self._split_fire(fire, lat_lngs)
                    fires.extend(split_fires)

            except Exception as e:
                logging.warn("Failed to consider fire for splitting emissions: %s", e)
                # Just add fire as is
                fires.append(fire)

        logging.info(f"Fires before splitting emissions: {len(self._fires)}; and after: {len(fires)}")
        return fires

    def _compute_max_emission_rate(self, fire):
        # Returns the max emissions rate for the fire - the max of the hourly
        # emissions values that get written to the EMISS.CFG file)
        max_rate = 0
        # We'll save max rate per hour, to be used in emissions allocation code
        fire['max_emiss_rate_per_hour'] = {}
        for dt_obj in fire.timeprofiled_emissions:
            dt = parse_datetime(dt_obj)
            rows, dummy = get_emissions_rows_data(fire, dt,
                self._config_getter, self._reduction_factor)

            max_rate_in_row = max([pm25 for (height, pm25, area, heat) in rows])
            fire['max_emiss_rate_per_hour'][dt_obj] = max_rate_in_row
            max_rate = max([max_rate, max_rate_in_row])

        return max_rate

    def _compute_new_lat_lngs(self, fire, num_split):
        """Creates an Archimedean spiral to place the new points

            r = a + b * theta

        Need to define the rate of increase of theta around the fire and the
        rate of increase of the distance from it
        """
        # start at the original source. this needs to update the original source with
        # the new emission rate (index zero) all of the following need to create a new
        # source
        lat_lngs = []
        r = 0
        theta = 0
        for i in range (num_split):
            x = r * math.cos( theta )
            y = r * math.sin( theta )

            theta += DTHETA
            r += DR

            lat_lngs.append([fire.latitude + y, fire.longitude + x])

        logging.info("Splitting emissions for fire centered at lat, lon %f, %f into %d -> %s",
            fire.latitude, fire.longitude, num_split, lat_lngs)
        return lat_lngs

    def _split_fire(self, fire, lat_lngs):
        num_split = len(lat_lngs)

        new_fires = []
        for i, lat_lng in enumerate(lat_lngs):
            f = Fire(
                id=f"{fire.id}-{i}",
                # TODO: how should original_fire_ids be assiend?
                original_fire_ids=fire.original_fire_ids,
                meta=fire.get('meta', {}),
                start=fire.start,
                end=fire.end,
                area=fire.area,  # fire.area / num_split,
                latitude=lat_lng[0],
                longitude=lat_lng[1],
                utc_offset=fire.utc_offset,
                plumerise=fire.plumerise,
                timeprofiled_emissions=self._allocate_emissions(fire, i),
                timeprofiled_area=fire.timeprofiled_area,
                consumption=self._get_reduced(fire, 'consumption', num_split),
            )

            if fire.heat:
                f.heat = fire.heat  #fire.heat / num_split

            new_fires.append(f)

        return new_fires

    def _allocate_emissions(self, fire, i):
        """Allocates emissions per hour, distributing to as few new fires as
        possible.
        """
        tpe = {}
        for dt in fire['timeprofiled_emissions']:
            # num_split_this_hr will never be greater than num_split, above,
            num_split_this_hr = max(1, math.ceil(fire['max_emiss_rate_per_hour'][dt]
                / self._emissions_rate_target))

            if i < num_split_this_hr:
                tpe[dt] = {species: val / num_split_this_hr
                    for species, val in fire['timeprofiled_emissions'][dt].items()}

            else:
                # assign all zeros
                tpe[dt] = {species: 0.0 for species in fire['timeprofiled_emissions'][dt]}

        return tpe

    def _get_reduced(self, fire, key, num_split):
        data = copy.deepcopy(fire[key])
        multiply_nested_data(data, 1 / num_split)
        return data
