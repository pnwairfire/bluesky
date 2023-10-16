import math

__all__ = [
    'EmissionsSplitter'
]

RADIANS_PER_DEGREE   = 0.01745329251994329576

class EmissionsSplitter():
    def __init__(self, config_getter, grid_params, num_traunches, fires):
        self._config_getter = config_getter
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
        import pdb;pdb.set_trace()

        if not self._config_getter('emissions_split', 'enabled'):
            return self._fires

        for fire in fires:
            # TODO: get input rate for the fire (based on max hourly
            #  emissions value?)
            RATE1 = 803200000

            # number of times to split the input rate
            NUMSPLIT = math.ceil(RATE1 / self._emissions_rate_target)

            # create an Archimedean spiral to place the new points
            # r = a + b * theta

            # need to define the rate of increase of theta around the fire and the
            # rate of increase of the distance from it

            # use a delta theta of 15 degrees (convert to radians) and a radius of 0.0005
            dtheta = 15.0 * RADIANS_PER_DEGREE
            dr =     0.0005
            # start at the original source. this needs to update the original source with
            # the new emission rate (index zero) all of the following need to create a new
            # source
            r     = 0

            print("FIRE CENTER LAT LON    %f %f" % ( fire.latitude, fire.longitude ))

            # loop over the number of sources (orig + extras)
            for i in range (NUMSPLIT):

              x = r * math.cos( theta )
              y = r * math.sin( theta )

              theta += dtheta
              r     += dr

              lonstar = x
              latstar = y

            # the new lat and lon of the split source (may need to do something to treat the orignal
            # source differently)
              newlat = fire.latitude + latstar
              newlon = fire.longitude + lonstar
