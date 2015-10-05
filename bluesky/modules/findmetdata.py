"""bluesky.modules.findmetdata

This module finds met data files to use for a particular domain and time window.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bluesky.met import arlfinder

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager, config=None):
    """runs the findmetdata module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    logging.info("Running findmetdata module")
    fires_manager.processed(__name__, __version__)

    # TODO: For playground, there will be only one file containing data for
    # any particular hour.  Allow config to specify using simplified logic
    # for this scenario.  Otherwise, use more complicated logic in
    # arlfinder.ArlFinder (or put both code paths in ArlFinder?)

    # Note: ArlFinder will raise an exception if met_root_dir is undefined
    # or is not a valid directory
    met_root_dir = config.get('localmet', [}).get('met_root_dir')
    arl_finder = arlfinder.ArlFinder(met_root_dir)
    for fire in fires_manager.fires:
        for g in fire.growth:
            tw = parse_datetimes(g, 'start', 'end')
            g['met_files'] = arl_finder.find(tw['start'], tw['end'])
