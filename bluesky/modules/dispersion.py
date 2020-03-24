"""bluesky.modules.dispersion

If running hysplit dispersion, you'll need to obtain hysplit and various
other executables. See the repo README.md for more information.
"""

__author__ = "Joel Dubowy"

import logging

from bluesky.config import Config
from bluesky.importutils import import_class
from bluesky.io import get_working_and_output_dirs
from bluesky.metutils import filter_met

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    model = Config().get('dispersion', 'model').lower()
    processed_kwargs = {}
    try:
        module, klass = import_class("bluesky.dispersers.{}".format(model),
            "{}Dispersion".format(model.upper()))

        start, num_hours = _get_time(fires_manager)
        met = filter_met(fires_manager.met, start, num_hours)

        disperser = klass(met)
        processed_kwargs.update({
            "{}_version".format(model): module.__version__
        })

        output_dir, working_dir = get_working_and_output_dirs(module_name)

        # further validation of start and num_hours done in 'run'
        dispersion_info = disperser.run(fires_manager, start,
            num_hours, output_dir, working_dir=working_dir)
        dispersion_info.update(model=model)
        # TODO: store dispersion into in summary?
        #   > fires_manager.summarize(disperion=disperser.run(...))
        fires_manager.dispersion = dispersion_info

        # TODO: add information about fires to processed_kwargs

    finally:
        fires_manager.processed(__name__, __version__, model=model,
            **processed_kwargs)

    # TODO: add information to fires_manager indicating where to find the hysplit output


SECONDS_PER_HOUR = 3600

def _get_time(fires_manager):
    start = Config().get('dispersion', 'start')
    num_hours = Config().get('dispersion', 'num_hours')

    if not start or num_hours is None:
        s = fires_manager.earliest_start # needed for 'start' and 'num_hours'
        if not s:
            raise ValueError("Unable to determine dispersion 'start'")
        if not start:
            start = s

        if not num_hours and start == s:
            e = fires_manager.latest_end # needed only for num_hours
            if e and e > s:
                num_hours = int((e - s).total_seconds() / SECONDS_PER_HOUR)
        if not num_hours:
            raise ValueError("Unable to determine dispersion 'num_hours'")

    logging.debug("Dispersion window: %s for %s hours", start, num_hours)
    return start, num_hours
