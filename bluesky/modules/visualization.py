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
        for obj in (visualization_info, processed_kwargs):
            obj['targets'].append({"target": target})

        try:
            model = get_model(fires_manager, target)
            for obj in (visualization_info, processed_kwargs):
                obj['targets'][-1].update({"model": model})
            module, klass = import_class(
                'bluesky.visualizers.{}.{}'.format(target, model),
                '{}{}Visualizer'.format(model.capitalize(), target.capitalize()))
            visualizer = klass(fires_manager)
            processed_kwargs['targets'][-1].update(
                version=module.__version__)

            visualization_info['targets'][-1].update(visualizer.run())
            # TODO: add information to fires_manager indicating where to
            #   find the hysplit output if hysplit dispersion

        except Exception as e:
            visualization_info['targets'][-1].update(error=str(e))

    # need top level output > directory information for export
    visualization_info["output"] = {"directories": []}
    for t in visualization_info["targets"]:
        if t.get('output',{}).get('directory'):
            visualization_info["output"]["directories"].append(
                t['output']['directory'])

    fires_manager.visualization = visualization_info
    fires_manager.processed(__name__, __version__, **processed_kwargs)


def get_targets():
    vis_config = Config().get('visualization')
    targets = vis_config['targets']

    # 'visualization' > 'target' supported for backwards compatibility
    if vis_config.get('target'):
        # this will only be hit if it's an older config specifying
        # 'visualization' > 'target'
        targets = [vis_config['target']]

    targets = [t.lower() for t in targets]
    logging.info("Visualizatin targets '%s'", "', '".join(targets))

    invalid = [t for t in targets if t not in vis_config]
    if invalid:
        raise ValueError("Invalid visualization target(s): '{}'".format(
            "','".join(invalid)))

    return targets

def get_model(fires_manager, target):
    model =  (getattr(fires_manager, target) or {}).get('model')
    model = model or Config().get(target, 'model')
    if model:
        return model.lower()

    raise ValueError("{} model must be specified if visualizing {}",
        target.capitalize(), target)
