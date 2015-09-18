"""bluesky.modules.consumption"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

from bluesky import datautils

__all__ = [
    'run'
]

__version__ = "0.1.0"

# TODO: These burn-type pecific settings sets might not be correct
# TODO: Check with Susan P, Susan O, Kjell, etc. to make sure defaults are correct
SETTINGS = {
    'natural': [],
    'activity': [
        ('slope', None),
        ('windspeed', None),
        ('days_since_rain', None),
        ('fuel_moisture_10hr_pct', 50), # default from consume package
        ('length_of_ignition', None),
        ('fm_type', None),
    ],
    'all': [
        ('fuel_moisture_1000hr_pct', 50), # default from consume package
        ('fuel_moisture_duff_pct', 50), # default from consume package
        ('canopy_consumption_pct', 0),
        ('shrub_blackened_pct', 50),
        ('output_units', None),
        ('pile_blackened_pct', 0)
    ]
}

def run(fires_manager, config=None):
    """Runs the fire data through consumption calculations, using the consume
    package for the underlying computations.

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    logging.debug("Running consumption module")
    # TODO: don't hard code consume_version; either update consume to define
    # it's version in consume.__version__, or execute pip:
    #   $ pip freeze |grep consume
    #  or
    #   $ pip show apps-consume4|grep "^Version:"
    fires_manager.processed(__name__, __version__,
        consume_version="4.1.2")

    # TODO: update bsp to have generic way of specifying module-specific
    # config, and get msg_level and burn_type from config
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError("Missing fuelbed data required for computing consumption")

        burn_type = 'activity' if fire.get('type') == "rx" else 'natural'
        valid_settings = SETTINGS[burn_type] + SETTINGS['all']

        # TODO: can I run consume on all fuelbeds at once and get per-fuelbed
        # results?  If it is simply a matter of parsing separated values from
        # the results, make sure that running all at once produces any performance
        # gain; if it doesn't, then it might not be worth the trouble
        for fb in fire.fuelbeds:
            fc = consume.FuelConsumption() #msg_level=msg_level)
            fc.burn_type = burn_type
            fc.fuelbed_fccs_ids = [fb['fccs_id']]

            # Note: if we end up running fc on all fuelbeds at once, use lists
            # for the rest
            fc.fuelbed_area_acres = [fb['pct'] * fire.location['area']]
            fc.fuelbed_ecoregion = [fire.location['ecoregion']]

            for k, default in valid_settings:
                if fire.location.has_key(k):
                    setattr(fc, k, fire.location[k])
                elif default is not None:
                    setattr(fc, k, default)

            if fc.results():
                fb['consumption'] = fc.results()['consumption']
                fb['consumption'].pop('debug', None)
            else:
                logging.error("Failed to calculate consumption for fire %s / %s fuelbed %s" % (
                    fire.id, fire.name, fb['fccs_id']
                ))
    fires_manager.summarize(consumption=datautils.summarize(fires_manager.fires))
