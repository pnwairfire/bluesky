"""bluesky.modules.archive"""

__author__ = "Joel Dubowy"

import logging

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.importutils import import_class

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """

    targets = get_targets()

    processed_kwargs = {"targets": []}
    visualization_info = {"targets": []}
    for target in targets:
        for obj in (visualization_info, processed_kwargs)
            obj['targets'].append({"target": target})
            obj['targets'][-1].update(model=model)

        try:
            model = get_model(fires_manager, target)
            module, klass = import_class(
                'bluesky.visualizers.{}.{}'.format(target, model),
                '{}Visualizer'.format(target.capitalize()))
            visualizer = klass(fires_manager)
                processed_kwargs['targets'][-1].update(
                    version=module.__version__)

            visualization_info['targets'][-1].update(visualizer.run())
            # TODO: add information to fires_manager indicating where to
            #   find the hysplit output if hysplit dispersion

        finally:
            fires_manager.visualization = visualization_info
            fires_manager.processed(__name__, __version__, **processed_kwargs)

def get_targets():
    targets = Config().get('visualization', 'targets')

    # 'visualization' > 'target' supported for backwards compatibility
    if Config().get('visualization', 'target'):
        # this will only be hit if it's an older config specifying
        # 'visualization' > 'target'
        targets = [Config().get('visualization', 'target')]

    targets = [t.lower() for t in targets]


def get_model(fires_manager, target):
    if target not in fires_manager and target not in Config().get():
        raise ValueError("Invalid visualization target: {}".format(target))

    model = fires_manager.get(target) and fires_manager[target].get('model')
    if model:
        return fires_manager[target]['model']

    model = Config().get(target, 'model')
    if model:
        return model.lower()

    raise ValueError("{} model must be specified if visualizing {}",
        target.capitalize(), target)
