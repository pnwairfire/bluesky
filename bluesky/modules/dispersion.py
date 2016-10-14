"""bluesky.modules.dispersion

If running hysplit dispersion, you'll need to obtain hysplit and various other
Executables. See the repo README.md for more information.
"""

__author__ = "Joel Dubowy"

import consume
import copy
import datetime
import importlib
import logging

from bluesky import datetimeutils
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.dispersers.hysplit import hysplit
from bluesky.datetimeutils import parse_datetime

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    model = fires_manager.get_config_value('dispersion', 'model',
        default='hysplit').lower()
    processed_kwargs = {}
    try:
        module, klass = _get_module_and_class(model)
        model_config = fires_manager.get_config_value(
            'dispersion', model, default={})

        start, num_hours = _get_time(fires_manager)

        # limit met to what covers
        end = start + datetime.timedelta(hours=num_hours)
        met = copy.deepcopy(fires_manager.met)
        met["files"] = [m for m in met["files"]
            if parse_datetime(m['first_hour']) <= end
            and parse_datetime(m['last_hour']) >= start]

        disperser = klass(met, **model_config)
        processed_kwargs.update({
            "{}_version".format(model): module.__version__
        })

        dest_dir, output_dir_name = _get_dirs(fires_manager)

        # further validation of start and num_hours done in 'run'
        dispersion_info = disperser.run(fires_manager.fires, start,
            num_hours, dest_dir, output_dir_name)
        dispersion_info.update(model=model)
        # TODO: store dispersion into in summary?
        #   > fires_manager.summarize(disperion=disperser.run(...))
        fires_manager.dispersion = dispersion_info

        # TODO: add information about fires to processed_kwargs

    finally:
        fires_manager.processed(__name__, __version__, model=model,
            **processed_kwargs)

    # TODO: add information to fires_manager indicating where to find the hysplit output


def _get_module_and_class(model):
    module_name = "bluesky.dispersers.{}".format(model)
    logging.debug("Importing %s", module_name)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise BlueSkyConfigurationError(
            "Invalid dispersion model: '{}'".format(model))

    klass_name = "{}Dispersion".format(model.upper())
    logging.debug("Loading class %s", klass_name)
    try:
        klass = getattr(module, klass_name)
    except:
        # TODO: use more appropriate exception class
        raise RuntimeError("{} does not define class {}".format(
            module_name, klass_name))

    return module, klass

SECONDS_PER_HOUR = 3600

def _get_time(fires_manager):
    start = fires_manager.get_config_value('dispersion', 'start')
    num_hours = fires_manager.get_config_value('dispersion', 'num_hours')

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


def _get_dirs(fires_manager):
    dest_dir = fires_manager.get_config_value('dispersion', 'dest_dir')
    if not dest_dir:
        raise ValueError("Specify directory to save dispersion run output")

    output_dir_name = (fires_manager.get_config_value('dispersion',
        'output_dir_name') or fires_manager.run_id)

    return dest_dir, output_dir_name
