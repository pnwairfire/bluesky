import logging
import math

from afdatetime.parsing import parse_datetime

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
        num_fires_per_traunche = len(self._fires)/num_traunches
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

        # target PM2.5 value (micrograms/m3)
        PM25star  = self._config_getter('emissions_split', 'target_pm25')

        # target mass per particle (grams)
        self._target_mass = PM25star * self._dx * self._dy * DZ / 1e6

    def _set_emissions_rate_target(self):
        # for each hour, if emissions exceed threshold, split emissions out
        # amongst minumum number of sublocations necessary to get per-location
        # emissions below threshold; if not all are needed, set those extra
        # locations to zero (some hours will require no re-allocation at all)

        # emission rate target
        self._emissions_rate_target = self._target_mass * self._numpar_per_src_per_timestep / self._deltsec

    ##
    ## Public API
    ##

    def split(self):
        if not self._config_getter('emissions_split', 'enabled'):
            return self._fires

        fires = []

        for fire in self._fires:
            try:
                max_emiss_rate = self._compute_emission_rate(fire)

                # number of times to split the input rate
                num_split = math.ceil(max_emiss_rate / self._emissions_rate_target)

                if num_split == 1:
                    fires.append(fire)

                else:
                    lat_lngs = self._compute_new_lat_lngs(fire, num_split)

            except Exception as e:
                logging.warn("Failed to consider fire for splitting emissions: %s", e)
                # Just add fire as is
                fires.append(fire)

    def _compute_emission_rate(self, fire):
        # TODO: get input rate for the fire (based on max hourly
        #  emissions value?)  <-- from Robert:  (it is essentially the
        #  value that gets written to the EMISS.CFG file)
        #RATE1 = 803200000
        max_rate = 0
        for dt in fire.timeprofiled_emissions:
            dt = parse_datetime(dt)
            rows, dummy = get_emissions_rows_data(fire, dt,
                self._config_getter, self._reduction_factor)

            max_rate = max([pm25 for (height, pm25, area, heat) in rows])

        return max_rate

    def _compute_new_lat_lngs(self, fire, num_split):
        """Creates an Archimedean spiral to place the new points

            r = a + b * theta

        Need to define the rate of increase of theta around the fire and the
        rate of increase of the distance from it
        """
        logging.info("Splitting emissions for fire centered at LAT LON %f %f",
            fire.latitude, fire.longitude)

        # start at the original source. this needs to update the original source with
        # the new emission rate (index zero) all of the following need to create a new
        # source
        lat_lngs = []
        r = 0
        for i in range (num_split):
            x = r * math.cos( theta )
            y = r * math.sin( theta )

            theta += DTHETA
            r += DR

            lat_lngs.append([fire.latitude + y, fire.longitude + x])

        return lat_lngs
