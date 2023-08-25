"""bluesky.consumption.consume.precomputed
"""

import csv
import logging
import os

import consume
import numpy

from .consumeutils import FuelLoadingsManager, ECO_REGION_BY_FCCS_ID, ALL_FCCS_IDS

__all__ = [
    'FIRE_TYPES',
    'BURN_TYPES',
    'SEASONS',
    'ACTIVITY_SETTINGS',
    # 'VARIABLE_ACTIVITY_SETTINGS',
    'OTHER_SETTINGS',
    'FM_INPUT_VALS',
    'precompute',
]


##
## Params
##

"""
We pre-compute CONSUME for every combination of the following parameters
  - FCCS Id
  - Fire type - 'rx', 'wildfire' (which determines values for
    'canopy_consumption_pct', 'shrub_blackened_pct', 'pile_blackened_pct',
    'duff_pct_available', 'sound_cwd_pct_available', and 'rotten_cwd_pct_available'
  - Burn (fire) type - 'natural', 'activity' (which determines
    which input fields are passed into CONSUME
  - Season - 'spring', 'summer', 'fall', 'winter'
  - 1000hr moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'
  - Duff moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'
  - Litter moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'

  That makes a total of num_fccs_ids * 2 * 2 * 3 * 4 * 6 * 6 * 6 = 3,525,120 combinations,
  and that only considers one value for 'fuel_moisture_10hr_pct' (which is used
  for activity burns and is defaulted to 50).

 Each combination produces an output set that looks like the following:

  {'parameters': {'ecoregion': ['western'], 'season': ['spring'], 'area': array([1.]), 'fuelbeds': ['1'], 'can_con_pct': array([0.]), 'shrub_black_pct': array([50.]), 'pile_black_pct': array([0.]), 'fm_1000hr': array([10.]), 'fm_duff': array([20.]), 'fm_litter': array([4.]), 'filename': array(['FB_0001_FCCS.xml'], dtype=object), 'burn_type': ['natural'], 'units': ['tons_ac']}, 'heat release': {'flaming': array([1.2184763e+08]), 'smoldering': array([1.52693402e+08]), 'residual': array([94351858.62525254]), 'total': array([3.6889289e+08])}, 'consumption': {'summary': {'total': {'flaming': array([7.61547686]), 'smoldering': array([9.54333762]), 'residual': array([5.89699116]), 'total': array([23.05580564])}, 'canopy': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'shrub': {'flaming': array([1.27311208]), 'smoldering': array([0.1414569]), 'residual': array([0.]), 'total': array([1.41456898])}, 'nonwoody': {'flaming': array([0.166932]), 'smoldering': array([0.018548]), 'residual': array([0.]), 'total': array([0.18548])}, 'litter-lichen-moss': {'flaming': array([0.92454395]), 'smoldering': array([0.09209701]), 'residual': array([0.]), 'total': array([1.01664097])}, 'ground fuels': {'flaming': array([0.94656]), 'smoldering': array([6.62592]), 'residual': array([1.89312]), 'total': array([9.4656])}, 'woody fuels': {'flaming': array([4.30432882]), 'smoldering': array([2.66531571]), 'residual': array([4.00387116]), 'total': array([10.9735157])}}, 'canopy': {'overstory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'midstory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'understory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 foliage': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 wood': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 no foliage': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 2': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 3': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'ladder fuels': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'shrub': {'primary live': {'flaming': array([1.27311208]), 'smoldering': array([0.1414569]), 'residual': array([0.]), 'total': array([1.41456898])}, 'secondary live': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'nonwoody': {'primary live': {'flaming': array([0.166932]), 'smoldering': array([0.018548]), 'residual': array([0.]), 'total': array([0.18548])}, 'secondary live': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'litter-lichen-moss': {'litter': {'flaming': array([0.74276937]), 'smoldering': array([0.08252993]), 'residual': array([0.]), 'total': array([0.8252993])}, 'lichen': {'flaming': array([0.00150227]), 'smoldering': array([7.9066804e-05]), 'residual': array([0.]), 'total': array([0.00158134])}, 'moss': {'flaming': array([0.18027231]), 'smoldering': array([0.00948802]), 'residual': array([0.]), 'total': array([0.18976033])}}, 'ground fuels': {'duff upper': {'flaming': array([0.94656]), 'smoldering': array([6.62592]), 'residual': array([1.89312]), 'total': array([9.4656])}, 'duff lower': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'basal accumulations': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'squirrel middens': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'woody fuels': {'piles': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'stumps sound': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'stumps rotten': {'flaming': array([0.00147025]), 'smoldering': array([0.00441075]), 'residual': array([0.0088215]), 'total': array([0.0147025])}, 'stumps lightered': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, '1-hr fuels': {'flaming': array([0.160911]), 'smoldering': array([0.008469]), 'residual': array([0.]), 'total': array([0.16938])}, '10-hr fuels': {'flaming': array([0.609768]), 'smoldering': array([0.067752]), 'residual': array([0.]), 'total': array([0.67752])}, '100-hr fuels': {'flaming': array([2.1202825]), 'smoldering': array([0.249445]), 'residual': array([0.1247225]), 'total': array([2.49445])}, '1000-hr fuels sound': {'flaming': array([0.3]), 'smoldering': array([0.15]), 'residual': array([0.05]), 'total': array([0.5])}, '1000-hr fuels rotten': {'flaming': array([0.50030151]), 'smoldering': array([0.75045226]), 'residual': array([1.25075377]), 'total': array([2.50150754])}, '10000-hr fuels sound': {'flaming': array([0.2]), 'smoldering': array([0.2]), 'residual': array([0.1]), 'total': array([0.5])}, '10000-hr fuels rotten': {'flaming': array([0.23418368]), 'smoldering': array([0.70255105]), 'residual': array([1.4051021]), 'total': array([2.34183684])}, '10k+-hr fuels sound': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, '10k+-hr fuels rotten': {'flaming': array([0.17741188]), 'smoldering': array([0.53223565]), 'residual': array([1.06447129]), 'total': array([1.77411882])}}}}

"""

FIRE_TYPES = ['rx', 'wildfire']
BURN_TYPES = ['natural', 'activity'] # a.k.a. 'fuel_type'
SEASONS = ['spring', 'summer', 'fall', 'winter']

# Activity settings are the same for rx and wildfire
ACTIVITY_SETTINGS = {
    'slope': 5,
    'windspeed': 6,
    'days_since_rain':  10,
    'length_of_ignition': 120,
    'fm_type': 'MEAS-Th',
    'fuel_moisture_10hr_pct': 50  # TODO: compute for each moisture level?
}
# VARIABLE_ACTIVITY_SETTINGS = {
#     'fuel_moisture_10hr_pct': { # normally defaults to 50
#         'very dry': ,
#         'dry': ,
#         'moderate': ,
#         'moist': ,
#         'wet': ,
#         'very wet':
#     },
# }

OTHER_SETTINGS = {
    'canopy_consumption_pct': {'rx': 0, 'wildfire': 0},
    'shrub_blackened_pct': {'rx': 50, 'wildfire': 50},
    'pile_blackened_pct': {'rx': 0, 'wildfire': 0},
    'duff_pct_available': {'rx': 5, 'wildfire': 10},
    'sound_cwd_pct_available': {'rx': 5, 'wildfire': 10},
    'rotten_cwd_pct_available': {'rx': 5, 'wildfire': 10}
}

FM_LEVELS = {

    # TODO: defaults for each moisture level shyould be per region
    #   from Ernesto:
    #      Th values depend on the regions. There are values for
    #      the NW (Ottmar’s work), there are also values for the
    #      SE (Dale Wade’s publications). The values are related
    #      to moisture of extinction.

    'fuel_moisture_1000hr_pct': [  # normal defualts: {'rx': 35, 'wildfire': 15},
        {'level': 'very dry', 'up_to': 12.5, 'input_val': 10},
        {'level': 'dry', 'up_to': 22.5, 'input_val': 15},
        {'level': 'moderate', 'up_to': 32.5, 'input_val': 30},
        {'level': 'moist', 'up_to': 37.5, 'input_val': 35},
        {'level': 'wet', 'up_to': 50.5, 'input_val': 40},
        {'level': 'very wet', 'up_to': None, 'input_val': 60}
    ],
    'fuel_moisture_duff_pct': [  # normal defualts: {'rx': 100, 'wildfire': 40},
        {'level': 'very dry', 'up_to': 30, 'input_val': 20},
        {'level': 'dry', 'up_to': 57.2, 'input_val': 40},
        {'level': 'moderate', 'up_to': 87.5, 'input_val': 75},
        {'level': 'moist', 'up_to': 115, 'input_val': 100},
        {'level': 'wet', 'up_to': 150, 'input_val': 130},
        {'level': 'very wet', 'up_to': None, 'input_val': 180}
    ],
    'fuel_moisture_litter_pct': [  # normal defualts: {'rx': 22, 'wildfire': 10},
        {'level': 'very dry', 'up_to': 7, 'input_val': 4},
        {'level': 'dry', 'up_to': 13, 'input_val': 10},
        {'level': 'moderate', 'up_to': 19, 'input_val': 16},
        {'level': 'moist', 'up_to': 26, 'input_val': 22},
        {'level': 'wet', 'up_to': 35, 'input_val': 30},
        {'level': 'very wet', 'up_to': None, 'input_val': 40}
    ],
}
FM_INPUT_VALS = {k: {} for k in FM_LEVELS}
for k in FM_LEVELS:
    FM_INPUT_VALS[k] = {}
    for e in FM_LEVELS[k]:
        FM_INPUT_VALS[k][e['level']] = e['input_val']

##
## Methods used during pre-computation and look-up
##

KEY_JOIN_CHAR = ';'

def create_key(fccs_id, thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    return KEY_JOIN_CHAR.join([
        fccs_id, thousand_hr_fm_level, duff_fm_level, litter_fm_level
    ])

HEADER_JOIN_CHAR = ';'

def nested_to_flat(nested_dict, parent_key=None):
    """Flattens the dict and converts numpy.ndarray values to scalars
    """
    items = []
    for k, v in nested_dict.items():
        new_key = parent_key + HEADER_JOIN_CHAR + k if parent_key else k
        if hasattr(v, 'keys'):
            items.extend(nested_to_flat(v, new_key).items())
        else:
            # Truncate precision to 2 decimal places; Note that we could
            # leave the value as a string (i.e. not cast back to float), but
            # that didn't seem to significantly affect performance
            items.append((new_key, float(f'{v[0]:.2f}')))
    return dict(items)

def flat_to_nested(flat_dict):
    """Reconstitutes nested dict structure with numpy.ndarray values, as
    originally returned by consume
    """
    nested_dict = {}
    for k in flat_dict:
        keys = k.split(HEADER_JOIN_CHAR)
        d = nested_dict
        prev = None
        for f in keys:
            d[f] = {} if f not in d else d[f]
            prev = d
            d = d[f]
        # TODO: is there a way to explicitly create an numpy.ndarray ?
        #    https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html
        prev[f] = numpy.array([float(flat_dict[k])])

    return nested_dict

def get_consumption_data_filename(fire_type, burn_type, season):
    return os.path.join(os.path.dirname(__file__), 'data',
        f"precomputed-consumption-{fire_type}-{burn_type}-{season}.csv")

def get_heat_data_filename(fire_type, burn_type, season):
    return os.path.join(os.path.dirname(__file__), 'data',
        f"precomputed-heat-{fire_type}-{burn_type}-{season}.csv")


##
## Generation of data
##

def run_consume(fire_type, burn_type, season, fccs_id,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    # It may be more efficient to create one FuelConsumption
    # object for all runs, but it's safer to start with a clean
    # slate for each run
    fc = consume.FuelConsumption()

    fc.burn_type = burn_type
    fc.season = [season]

    #fb['fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)

    # ecoregion was determined, per FCCS Id,  from consume's fuel loadings file
    fc.fuelbed_ecoregion = [ECO_REGION_BY_FCCS_ID[fccs_id]]
    fc.fuelbed_fccs_ids = [fccs_id]
    fc.fuelbed_area_acres = [1]

    # According to comments in consume, some of the inputs can be set as either
    # lists or scalars. We're assuming the following are all ok to be set as scalars.

    if burn_type == 'activity':
        for k, v in ACTIVITY_SETTINGS.items():
            setattr(fc, k, v)

    for k, vDict in OTHER_SETTINGS.items():
        #logging.debug("Setting %s to %s", k, vDict[fire_type])
        try:
            setattr(fc, k, vDict[fire_type])
        except Exception as e:
            logging.warn("Failed to set %s: %s", k, e)

    fc.fuel_moisture_1000hr_pct = FM_INPUT_VALS['fuel_moisture_1000hr_pct'][thousand_hr_fm_level]
    fc.fuel_moisture_duff_pct = FM_INPUT_VALS['fuel_moisture_duff_pct'][duff_fm_level]
    fc.fuel_moisture_litter_pct = FM_INPUT_VALS['fuel_moisture_litter_pct'][litter_fm_level]

    r = fc.results()
    r['consumption'].pop('debug', None)

    return r

def get_fieldnames():
    nested_results = run_consume(FIRE_TYPES[0], BURN_TYPES[0],
        SEASONS[0], ALL_FCCS_IDS[0],
        list(FM_INPUT_VALS['fuel_moisture_1000hr_pct'])[0],
        list(FM_INPUT_VALS['fuel_moisture_duff_pct'])[0],
        list(FM_INPUT_VALS['fuel_moisture_litter_pct'])[0])

    flat_cons = nested_to_flat(nested_results['consumption'])

    flat_heat = nested_to_flat(nested_results['heat release'])


    return ['key'] + list(flat_cons), ['key'] + list(flat_heat)

def precompute_file(fire_type, burn_type, season, cons_fieldnames,
        heat_fieldnames, fccs_ids):
    fccs_ids = fccs_ids or ALL_FCCS_IDS
    cons_filename = get_consumption_data_filename(fire_type, burn_type, season)
    heat_filename = get_heat_data_filename(fire_type, burn_type, season)

    with open(cons_filename, 'w') as cons_csvfile:
        with open(heat_filename, 'w') as heat_csvfile:
            # run consume once to get field names
            cons_writer = csv.DictWriter(cons_csvfile, fieldnames=cons_fieldnames)
            cons_writer.writeheader()

            heat_writer = csv.DictWriter(heat_csvfile, fieldnames=heat_fieldnames)
            heat_writer.writeheader()

            for fccs_id in fccs_ids:
                for thousand_hr_fm_level in FM_INPUT_VALS['fuel_moisture_1000hr_pct']:
                    for duff_fm_level in FM_INPUT_VALS['fuel_moisture_duff_pct']:
                        for litter_fm_level in FM_INPUT_VALS['fuel_moisture_litter_pct']:
                            nested_results = run_consume(fire_type,
                                burn_type, season,
                                fccs_id, thousand_hr_fm_level,
                                duff_fm_level, litter_fm_level)
                            key = create_key(fccs_id, thousand_hr_fm_level,
                                duff_fm_level, litter_fm_level)

                            flat_cons = nested_to_flat(nested_results['consumption'])
                            flat_cons['key'] = key
                            cons_writer.writerow(flat_cons)

                            flat_heat = nested_to_flat(nested_results['heat release'])
                            flat_heat['key'] = key
                            heat_writer.writerow(flat_heat)

def precompute(options):
    cons_fieldnames, heat_fieldnames = get_fieldnames()

    fire_types = [options.fire_type.lower()] if options.fire_type else FIRE_TYPES
    burn_types = [options.burn_type.lower()] if options.burn_type else BURN_TYPES
    seasons = [options.season.lower()] if options.season else SEASONS

    for fire_type in fire_types:
        for burn_type in burn_types:
            for season in seasons:
                precompute_file(fire_type, burn_type, season, cons_fieldnames,
                    heat_fieldnames, options.fccs_ids)


##
## Reading
##


class ConsumeLookup(object):
    """Class for managing bluesky configuration.

    This is a Singleton, so that data are loaded only once
    """

    instances = {}

    def __new__(cls, fire_type, burn_type, season):
        i_key = '-'.join([fire_type, burn_type, season])
        if i_key not in cls.instances:
            cls.instances[i_key] = super(ConsumeLookup, cls).__new__(cls)
        return cls.instances[i_key]

    def __init__(self, fire_type, burn_type, season):
        self._load(fire_type, burn_type, season)

    def _load(self, fire_type, burn_type, season):
        if not hasattr(self, '_consumption_data'):
            self._consumption_data = self._load_file(
                get_consumption_data_filename(fire_type, burn_type, season))
        if not hasattr(self, '_heat_data'):
            self._heat_data = self._load_file(
                get_heat_data_filename(fire_type, burn_type, season))

    def _load_file(self, filename):
        data = {}

        logging.info("Loading %s data", filename)
        with open(filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.pop('key')
                data[key] = flat_to_nested(row)
        logging.info("Finished loading %s", filename)

        return data

    def get(self, key):
        return self._consumption_data[key], self._heat_data[key]

SEASONAL_FM_LEVELS = {
    'spring': 'moist',
    'summer': 'dry',
    'fall': 'moderate',
    'winter': 'dry' #???
}
def get_fm_level(key, fm_val, season):
    if not fm_val:
        return SEASONAL_FM_LEVELS[season.lower()]

    for l in FM_LEVELS[key]:
        if not l['up_to'] or fm_val < l['up_to']:
            return l['level']
    # Should never get here, since the last level should have 'up_to' set
    # to None, but just in case it's accidentally defined, just
    # return the last level
    return l['level']

def look_up(fccs_id, fire_type, burn_type, season,
        thousand_hr_fm, duff_fm, litter_fm):
    fire_type = fire_type.lower()
    burn_type = burn_type.lower()
    season = season.lower()

    if fccs_id not in ALL_FCCS_IDS:
        raise RuntimeError(f"Invalid FCCS Id {fccs_id}")
    if fire_type not in FIRE_TYPES:
        raise RuntimeError(f"Invalid fire type {fire_type}")
    if burn_type not in BURN_TYPES:
        raise RuntimeError(f"Invalid burn type {burn_type}")
    if season not in SEASONS:
        raise RuntimeError(f"Invalid season {season}")

    thousand_hr_fm_level = get_fm_level('fuel_moisture_1000hr_pct', thousand_hr_fm, season)
    duff_fm_level = get_fm_level('fuel_moisture_duff_pct', duff_fm, season)
    litter_fm_level = get_fm_level('fuel_moisture_litter_pct', litter_fm, season)

    logging.debug("100hr FM %s -> %s", thousand_hr_fm, thousand_hr_fm_level)
    logging.debug("Duff FM %s -> %s", duff_fm, duff_fm_level)
    logging.debug("Litter FM %s -> %s", litter_fm, litter_fm_level)

    key = create_key(fccs_id, thousand_hr_fm_level,
        duff_fm_level, litter_fm_level)

    return ConsumeLookup(fire_type, burn_type, season).get(key)
