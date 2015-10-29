"""bluesky.modules.archive"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

from bluesky import visualizers
from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    target = fires_manager.get_config_value('visualization', 'target',
        default='dispersion').lower()
    processed_kwargs = {"target": target}
    visualization_info = {"target": target}
    try:
        # TODO: support VSMOKE as well
        if target == 'dispersion':
            if not fires_manager.dispersion or not fires_manager.dispersion.get('model'):
                raise ValueError("Dispersion model must be specified if visualizing dispersion")
            if not fires_manager.dispersion or not fires_manager.dispersion.get('output'):
                raise ValueError("Dispersion output information must be specified if visualizing dispersion")
            dispersion_model = fires_manager.dispersion['model']
            processed_kwargs.update(dispersion_model=dispersion_model)
            visualization_info.update(dispersion_model=dispersion_model)
            if dispersion_model == 'hysplit':
                hysplit_visualization_config = fires_manager.get_config_value(
                    'visualization', 'hysplit', default={})
                visualizer = visualizers.dispersion.hysplit.HysplitVisualizer(
                    fires_manager.dispersion['output'], fires_manager.fires,
                    **hysplit_visualization_config)
                processed_kwargs.update(
                    hysplit_visualizer_version=visualizers.dispersion.hysplit.__version__)
            else:
                NotImplementedError("Visualization of {} dispersion model not "
                    "supported".format(dispersion_model))

        else:
            raise BlueSkyConfigurationError(
                "Invalid visualizaton: '{}'".format(model))

        visualization_info.update(visualizer.run())
        fires_manager.visualization = visualization_info

    finally:
        fires_manager.processed(__name__, __version__, **processed_kwargs)

    # TODO: add information to fires_manager indicating where to find the hysplit output
