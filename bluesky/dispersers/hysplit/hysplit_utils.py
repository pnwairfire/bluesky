"""bluesky.dispersers.hysplit.hysplit_utils

Generic hysplit utility module created in large part for ease of testing

TODO: refactor this as a class
"""

__author__ = "Joel Dubowy and Sonoma Technology, Inc."

import logging
import math
from functools import reduce


__all__ = [
    'create_fire_sets', 'create_fire_tranches'
    ]

def create_fire_sets(fires):
    """Creates sets of fires, grouping by location

    A single fire location may show up multiple times if it lasted multiple days,
    since there's one FireLocationData per location per day.  We don't want to
    split up any location into multiple tranches, so we'll group FireLocationData
    objects by location id and then tranche the location fire sets.

    @todo: make sure fire locations from any particular event don't get split up into
      multiple HYSPLIT runs ???  (use fires[N]['metadata']['sf_event_guid']) ?
    """

    fires_dict = {e: [] for e in set([f.id for f in fires])}
    for f in fires:
        fires_dict[f.id].append(f)
    return  list(fires_dict.values())

def create_fire_tranches(fire_sets, num_processes):
    """Creates tranches of FireLocationData, each tranche to be processed by its
    own HYSPLIT process.

    @todo: More sophisticated tranching (ex. taking into account acreage, location, etc.).
    """

    n_sets = len(fire_sets)
    num_processes = min(n_sets, num_processes)  # just to be sure
    min_n_fire_sets_per_process = n_sets // num_processes
    extra_fire_cutoff = n_sets % num_processes

    logging.info("Running %d HYSPLIT49 Dispersion model processes "
        "on %d fires (i.e. events)" % (num_processes, n_sets))
    logging.info(" - %d processes with %d fires" % (
        num_processes - extra_fire_cutoff, min_n_fire_sets_per_process))
    if extra_fire_cutoff > 0:
        logging.info(" - %d processes with %d fires" % (
            extra_fire_cutoff, min_n_fire_sets_per_process+1))

    idx = 0
    fire_tranches = []
    for nproc in range(num_processes):
        s = idx
        idx += min_n_fire_sets_per_process
        if nproc < extra_fire_cutoff:
            idx += 1
        tranche_fire_sets = fire_sets[s:idx]
        logging.debug("Process %d:  %d fire sets" % (nproc, len(tranche_fire_sets)))
        fires = reduce(lambda x,y: x + y, tranche_fire_sets)
        fire_tranches.append(fires)
    return fire_tranches

def compute_num_processes(num_fire_sets, **config):
    """Determines number of HYSPLIT tranches given the number of fires sets
    and various tranching related config variables.

    Args:
     - num_fire_sets -- number of sets of fires, each set represeting a fire over
       possibly multiple days

    Config options:
     - num_processes -- if specified and greater than 0, this value is returned
     - num_fires_per_process -- if num_processes isn't specified and this value
       is (and is greater than 0), then the num_processes is set to the min value
       such that not process has more than num_fires_per_process fires (unless
       num_processes_max, below, is specified)
     - num_processes_max -- max number of processes; only comes into play if
       num_processes isn't specified but num_fires_per_process is, and
       num_fires_per_process is greater than num_processes_max
    """
    if 1 <= config.get('num_processes', 0):
        num_processes = min(num_fire_sets, config['num_processes'])
    elif 1 <= config.get('num_fires_per_process', 0):
        num_processes = math.ceil(float(num_fire_sets) / config['num_fires_per_process'])
        if 1 <= config.get('num_processes_max', 0):
            num_processes = min(num_processes, config['num_processes_max'])
    else:
        num_processes = 1

    return int(num_processes)


KM_PER_DEG_LAT = 111
DEG_LAT_PER_KM = 1.0 / KM_PER_DEG_LAT
RADIANS_PER_DEG = math.pi / 180.0
KM_PER_DEG_LNG_AT_EQUATOR = 111.32

def km_per_deg_lng(lat):
    return KM_PER_DEG_LNG_AT_EQUATOR * math.cos(RADIANS_PER_DEG * lat)

def square_grid_from_lat_lng(lat, lng, spacing_latitude,
        spacing_longitude, length, input_spacing_in_degrees=False):
    """Computes

    args
     - lat -- latitude of grid center
     - lng -- longitude of grid center
     - spacing_latitude -- height of grid cell, in km or degrees lat
     - spacing_longitude -- width of grid cell, in km or degrees lon
     - length -- length of each side of grid, in km
     - input_spacing_in_degrees -- by default, assumes spacing is in km
    """
    logging.debug("calculating {length}x{length} grid with lat/lng "
        "spacing {sp_lat}/{sp_lng} {spacing_unit} around {lat},{lng}".format(
        length=length, sp_lat=spacing_latitude, sp_lng=spacing_longitude,
        spacing_unit='degrees' if input_spacing_in_degrees else 'km',
        lat=lat, lng=lng))
    k_p_lng = km_per_deg_lng(lat)
    if not input_spacing_in_degrees:
        # convert from km to lat/lng; all other projections
        # are assumed to be spaced in km
        spacing_latitude /= KM_PER_DEG_LAT
        spacing_longitude /= k_p_lng
    d = {
        "center_latitude": lat,
        "center_longitude": lng,
        "height_latitude": DEG_LAT_PER_KM * length, # height in degrees
        "width_longitude": length / k_p_lng,  # width in degrees
        "spacing_longitude": spacing_longitude, # grid width in degrees
        "spacing_latitude": spacing_latitude # grid height in degrees
    }
    # TODO: truncate grid to keep from crossing pole? equator?
    return d

def grid_params_from_grid(grid, met_info={}):
    """
    Note: this function does not support boundaries spanning the
    international date line.  (i.e. NE lng > SW lng)
    """
    logging.info("Calculating grid parameters form boundary and spacing.")

    if not grid:
        raise ValueError("Dispersion grid must be defined either in the "
            "config or in the top level met object.")
    projection = grid.get('projection', met_info.get('projection'))
    spacing = grid.get('spacing', met_info.get('spacing'))
    if not spacing:
        raise ValueError("grid spacing must be defined either in user "
            "defined grid or in met object.")
    grid_boundary = grid.get('boundary', met_info.get('boundary'))
    if not grid_boundary:
        raise ValueError("grid boundary must be defined either in user "
            "defined grid or in met object.")
    # TODO: check that sw and ne lat/lng's are defined

    # TODO: support crossing international date line?
    if grid_boundary['sw']['lng'] >= grid_boundary['ne']['lng']:
        raise ValueError("grid boundaries spanning internation "
            "date line or with zero width not supported.")
    if grid_boundary['sw']['lat'] >= grid_boundary['ne']['lat']:
        raise ValueError("SW lat must be less than NE lat.")

    lat_center = (grid_boundary['sw']['lat'] + grid_boundary['ne']['lat']) / 2
    lng_center = (grid_boundary['sw']['lng'] + grid_boundary['ne']['lng']) / 2
    height_lat = grid_boundary['ne']['lat'] - grid_boundary['sw']['lat']
    width_lng = grid_boundary['ne']['lng'] - grid_boundary['sw']['lng']
    if projection != "LatLon":
        spacing = spacing / km_per_deg_lng(lat_center)

    return {
        "spacing_latitude": spacing,
        "spacing_longitude": spacing,
        "center_latitude": lat_center,
        "center_longitude": lng_center,
        "height_latitude": height_lat,
        "width_longitude": width_lng
    }

def get_grid_params(config, met_info={}, fires=None, allow_undefined=False):
    # If not specified, projection is assumed to be 'LatLon'
    is_deg = (config('projection') or 'LatLon') == 'LatLon'

    if config("USER_DEFINED_GRID"):
        # This supports BSF config settings
        # User settings that can override the default concentration grid info
        logging.info("User-defined sampling/concentration grid invoked")
        grid_params = {
            "center_latitude": config("CENTER_LATITUDE"),
            "center_longitude": config("CENTER_LONGITUDE"),
            "height_latitude": config("HEIGHT_LATITUDE"),
            "width_longitude": config("WIDTH_LONGITUDE"),
            "spacing_longitude": config("SPACING_LONGITUDE"),
            "spacing_latitude": config("SPACING_LATITUDE")
        }
        # BSF assumed lat/lng if USER_DEFINED_GRID; this support km spacing
        if not is_deg:
            grid_params["spacing_longitude"] /= hysplit_utils.km_per_deg_lng(
                grid_params["center_latitude"])
            grid_params["spacing_latitude"] /= hysplit_utils.KM_PER_DEG_LAT

    elif config('grid'):
        grid_params = hysplit_utils.grid_params_from_grid(
            config('grid'), met_info)

    elif config('compute_grid'):
        if not fires or len(fires) != 1:
            # TODO: support multiple fires
            raise ValueError("Option to compute grid only supported for "
                "runs with one fire")
        if (not config('spacing_latitude')
                or not config('spacing_longitude')):
            raise BlueSkyConfigurationError("Config settings "
                "'spacing_latitude' and 'spacing_longitude' required "
                "to compute hysplit grid")
        grid_params = hysplit_utils.square_grid_from_lat_lng(
            fires[0]['latitude'], fires[0]['longitude'],
            config('spacing_latitude'), config('spacing_longitude'),
            config('grid_length'), input_spacing_in_degrees=is_deg)

    elif met_info and met_info.get('grid'):
        grid_params = hysplit_utils.grid_params_from_grid(
            met_info['grid'], met_info)

    elif allow_undefined:
        grid_params = {}

    else:
        raise BlueSkyConfigurationError("Specify hysplit dispersion grid")

    logging.debug("grid_params: %s", grid_params)

    return grid_params