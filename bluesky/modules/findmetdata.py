"""bluesky.modules.findmetdata

This module finds met data files to use for a particular domain and time window
spanning all fire growth periods.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

from bluesky.met import arlfinder

from bluesky.datetimeutils import parse_datetimes

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """runs the findmetdata module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running findmetdata module")
    fires_manager.processed(__name__, __version__)

    # TODO: For playground, there will be only one file containing data for
    # any particular hour.  Allow config to specify using simplified logic
    # for this scenario.  Otherwise, use more complicated logic in
    # arlfinder.ArlFinder (or put both code paths in ArlFinder?)

    # Note: ArlFinder will raise an exception if met_root_dir is undefined
    # or is not a valid directory
    # TODO: specify domain instead of met_root_dir, and somehow configure (not
    # in the code, since this is open source), per domain, the root dir, arl file
    # name pattern, etc.
    met_root_dir = fires_manager.get_config_value('findmetdata',
        'met_root_dir')
    if not met_root_dir:
        raise BlueSkyConfigurationError("Config setting 'met_root_dir' "
            "required by findmetdata module".format(e.message))

    met_format = fires_manager.get_config_value('findmetdata', 'met_format',
        default="arl").lower()
    if met_format == arl:
        arl_config = fires_manager.get_config_value('findmetdata', 'arl',
            default={})
        arl_finder = arlfinder.ArlFinder(met_root_dir, **arl_config)
    else:
        raise BlueSkyConfigurationError(
            "Invalid or unsupported met data format: '{}'".format(met_format))

    # Find earliest and latest datetimes that include all fire growth periods
    # TODO: be more intelligent with possible gaps, so that met files for times
    #  when no fire is growing are excluded ?
    earliest = None
    latest = None
    for fire in fires_manager.fires:
        # parse_utc_offset makes sure utc offset is defined and valid
        utc_offset = parse_utc_offset(fire.get('location', {}).get('utc_offset'))
        for g in fire.growth:
            tw = parse_datetimes(g, 'start', 'end')
            if tw['start'] > tw['end']:
                raise ValueError("Invalid growth time window - start: {}, end: {}".format(
                    tw['start'], tw['end']))
            start = tw['start'] - utc_offset
            end = tw['end'] - utc_offset
            earlist = min(earliest, start)
            latest = max(latest, end)

    fires_manager.met = arl_finder.find(earliest, latest)
