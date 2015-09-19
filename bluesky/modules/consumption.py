"""bluesky.modules.consumption"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import tempfile
from collections import defaultdict

import consume

from bluesky import datautils
from bluesky.configuration import get_config_value

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


def _get_fuel_loadings(fccs_id, fccsdb_obj=None):
    # TODO: make sure this method works both when default fuel loadings
    # are used and when custom ones are used

    if not fccsdb_obj:
        fccsdb_obj = consume.fccs_db.FCCSDB()

    # iterate through the rows in the fccsdb_obj.loadings_data_
    # pandas.DataFrame until you find row with fuel loadings for fccs_id
    for i in range(len(fccsdb_obj.loadings_data_)):
        row = fccsdb_obj.loadings_data_.irow(i)
        if row[0] == str(fccs_id):
            return dict(row)

# TODO: come up with more elegant way to return mock file object with
# empty string name
class MockFuelLoadingsFile(object):
    name = ""

NON_LOADINGS_FIELDS = [
    'filename','cover_type','ecoregion','efg_natural','efg_activity'
]
FCCS_LOADINGS_CSV_HEADER = """GeneratorName=FCCS 3.0,GeneratorVersion=3.0.0,DateCreated=11/14/2014
fuelbed_number,filename,cover_type,ecoregion,overstory_loading,midstory_loading,understory_loading,snags_c1_foliage_loading,snags_c1wo_foliage_loading,snags_c1_wood_loading,snags_c2_loading,snags_c3_loading,shrubs_primary_loading,shrubs_secondary_loading,shrubs_primary_perc_live,shrubs_secondary_perc_live,nw_primary_loading,nw_secondary_loading,nw_primary_perc_live,nw_secondary_perc_live,w_sound_0_quarter_loading,w_sound_quarter_1_loading,w_sound_1_3_loading,w_sound_3_9_loading,w_sound_9_20_loading,w_sound_gt20_loading,w_rotten_3_9_loading,w_rotten_9_20_loading,w_rotten_gt20_loading,w_stump_sound_loading,w_stump_rotten_loading,w_stump_lightered_loading,litter_depth,litter_loading,lichen_depth,lichen_loading,moss_depth,moss_loading,basal_accum_loading,squirrel_midden_loading,ladderfuels_loading,duff_lower_depth,duff_lower_loading,duff_upper_depth,duff_upper_loading,pile_clean_loading,pile_dirty_loading,pile_vdirty_loading,Total_available_fuel_loading,efg_natural,efg_activity
"""
FCCS_LOADINGS_CSV_ROW_TEMPLATE = """{fuelbed_number},{filename},{cover_type},{ecoregion},{overstory_loading},{midstory_loading},{understory_loading},{snags_c1_foliage_loading},{snags_c1wo_foliage_loading},{snags_c1_wood_loading},{snags_c2_loading},{snags_c3_loading},{shrubs_primary_loading},{shrubs_secondary_loading},{shrubs_primary_perc_live},{shrubs_secondary_perc_live},{nw_primary_loading},{nw_secondary_loading},{nw_primary_perc_live},{nw_secondary_perc_live},{w_sound_0_quarter_loading},{w_sound_quarter_1_loading},{w_sound_1_3_loading},{w_sound_3_9_loading},{w_sound_9_20_loading},{w_sound_gt20_loading},{w_rotten_3_9_loading},{w_rotten_9_20_loading},{w_rotten_gt20_loading},{w_stump_sound_loading},{w_stump_rotten_loading},{w_stump_lightered_loading},{litter_depth},{litter_loading},{lichen_depth},{lichen_loading},{moss_depth},{moss_loading},{basal_accum_loading},{squirrel_midden_loading},{ladderfuels_loading},{duff_lower_depth},{duff_lower_loading},{duff_upper_depth},{duff_upper_loading},{pile_clean_loading},{pile_dirty_loading},{pile_vdirty_loading},{total_available_fuel_loading},{efg_natural},{efg_activity}
"""
def _generate_fuel_loadings_csv(config, fccs_id):
    all_fuel_loadings = get_config_value(config, 'consumption', 'fuel_loadings')
    if not all_fuel_loadings or not all_fuel_loadings.get('fccs_id'):
        # To indicate that consume's built-in fuel loadings should be used,
        # consume.FuelConsumption must be instantiated with fccs_file=""
        return MockFuelLoadingsFile

    # TODO: copy all_fuel_loadings['fccs_id'] dict so that we don't modify
    # original, below (?)
    fuel_loadings = all_fuel_loadings['fccs_id']

    # TODO: keep track of files already created in order to not create
    # redundant files?  (would need to restructure code to do so, such as
    # by creating a dict mapping fccs_id to tempfile object at the beginning
    # of 'run' and passing it into this function, which would grab existin
    # file or create and add new. this would prevent files form being
    # deleted until run completes.)

    f = tempfile.NamedTemporaryFile()

    f.write(FCCS_LOADINGS_CSV_HEADER)
    # set fuelbed_id
    fuel_loadings['fuelbed_number'] = fccs_id
    # default non-loadings columns to empty string
    for k in NON_LOADINGS_FIELDS:
        fuel_loadings[k] = fuel_loadings.get(k, "")
    # default loadings columns to 0.0
    fuel_loadings = defaultdict(lambda: 0.0, fuel_loadings)

    f.write(FCCS_LOADINGS_CSV_ROW_TEMPLATE.format(fuel_loadings))

    # return temp file object, not just it's name, since file is
    # deleted once obejct goes out of scope
    return f

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
            fuel_loadings_csv_filename = _generate_fuel_loadings_csv(config, fb['fccs_id'])
            fc = consume.FuelConsumption(fccs_file=fuel_loadings_csv_filename.name) #msg_level=msg_level)

            fb['fuel_loadings'] = _get_fuel_loadings(fb['fccs_id'], fc.FCCS)

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
    fires_manager.summarize(consumption=datautils.summarize(fires_manager.fires, 'consumption'))
