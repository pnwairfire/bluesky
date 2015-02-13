"""bluesky.modules.consumption
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

def run(fires):
    logging.debug("Running consumption module (NOOP)")

    # TODO: update bsp to have generic way of specifying module-specific
    # options, and get msg_level and burn_type from options
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires?
    for fire in fires:
        burn_type = 'activity' if fire.get('type') == "rx" else 'natural'
        fc = consume.FuelConsumption() #msg_level=msg_level)
        fc._settings.burn_type = burn_type
        fc.fuelbed_fccs_ids = [fb['fccs_id'] for fb in fire.fuelbeds]
        fc.fuelbed_area_acres = [fb['percentage'] * fire.area for fb in fire.fuelbeds]
        # >>> fc.fuelbed_ecoregion = 'western'
        # >>> fc.fuel_moisture_1000hr_pct = [50, 40]
        #fc.fuel_moisture_duff_pct = [50, 40]
        # >>> fc.canopy_consumption_pct = 25
        # >>> fc.shrub_blackened_pct = 25
        # >>> fc.output_units = 'kg_ha'
        # >>> fc.display_inputs()

        #fc.results()
        # fuelbed_list = consumer.fuelbed_fccs_ids
