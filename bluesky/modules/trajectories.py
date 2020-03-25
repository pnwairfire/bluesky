"""bluesky.modules.trajectories

If running hysplit trajectories, you'll need to obtain hysplit and various
other executables. See the repo README.md for more information.
"""

__author__ = "Joel Dubowy"

import logging

from bluesky.config import Config
from bluesky.datetimeutils import parse_datetime
from bluesky.importutils import import_class
from bluesky.io import get_working_and_output_dirs

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    model = Config().get('trajectories', 'model').lower()
    processed_kwargs = {}
    try:
        # e.g. 'hysplt' -> 'HysplitDispersion', 'foo_bar' -> 'FooBarDispersion'
        klass_name = ''.join(["{}Trajectories".format(m.capitalize())
            for m in model.split('_')])
        module, klass = import_class(
            "bluesky.trajectories.{}".format(model), klass_name)

        processed_kwargs.update({
            "{}_version".format(model): module.__version__
        })
        start, num_hours = _get_time_window()
        output_dir, working_dir = get_working_and_output_dirs('trajectories')

        traj_gen = klass(Config().get('trajectories', model))
        traj_info = traj_gen.run(fires_manager, start, num_hours,
            output_dir, working_dir=working_dir)
        traj_info.update(model=model)
        # TODO: store trajectories into in summary?
        #   > fires_manager.summarize(trajectories=disperser.run(...))
        fires_manager.trajectories = traj_info

        # TODO: add information about fires to processed_kwargs

    finally:
        fires_manager.processed(__name__, __version__, model=model,
            **processed_kwargs)

    # TODO: add information to fires_manager indicating where to find the hysplit output


def _get_time_window():
    start = Config().get('trajectories', 'start')
    if not start:
        raise BlueSkyConfigurationError(
            "Missing trajectories 'start' time")

    num_hours = Config().get('trajectories', 'num_hours')

    return parse_datetime(start), num_hours
