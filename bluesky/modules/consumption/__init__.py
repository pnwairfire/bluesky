"""bluesky.modules.consumption
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

# TODO: These burn-type pecific settings sets might not be correct
# TODO: Check with Susan P, Susan O, Kjell, etc. to make sure defaults are correct
SETTINGS = {
    'natural': [],
    'activity': [
        ('slope', None),
        ('windspeed', None),
        ('fm_type', None),
        ('fuel_moisture_10hr_pct', 50), # default from consume package
        ('length_of_ignition', None),
        ('days_since_rain', None),
        ('fm_type', None),
    ],
    'all': [
        ('fuel_moisture_1000hr_pct', 50), # default from consume package
        ('canopy_consumption_pct', 0),
        ('fuel_moisture_duff_pct', 50), # default from consume package
        ('shrub_blackened_pct', 50),
        ('output_units', None),
        ('pile_blackened_pct', 0)
    ]
}

def run(fires):
    logging.debug("Running consumption module (NOOP)")

    # TODO: update bsp to have generic way of specifying module-specific
    # options, and get msg_level and burn_type from options
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires:
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

            # Note: for the rest, use lists if we end up running fc on
            # all fuelbeds at once
            fc.fuelbed_area_acres = fb['pct'] * fire.area
            fc.fuelbed_ecoregion = [fire.ecoregion]

            for k, default in valid_settings:
                if fire.has_key(k):
                    setattr(fc, k, fire[k])
                elif default is not None:
                    setattr(fc, k, default)

            if fc.results():
                fb['consumption'] = fc.results()['consumption']
            else:
                logging.error("Failed to calculate consumption for fire %s / %s fuelbed %s" % (
                    fire.id, fire.name, fb['fccs_id']
                ))
