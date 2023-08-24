"""bluesky.consumption.consume.precomputed
"""

import csv
import logging
import os

import consume
import numpy

from .consumeutils import FuelLoadingsManager, ECO_REGION_BY_FCCS_ID

__all__ = [
    'FCCS_GROUPS',
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
  - FCCS Group
  - Fire type - 'rx', 'wildfire' (which determines values for
    'canopy_consumption_pct', 'shrub_blackened_pct', 'pile_blackened_pct',
    'duff_pct_available', 'sound_cwd_pct_available', and 'rotten_cwd_pct_available'
  - Burn (fire) type - 'natural', 'activity' (which determines
    which input fields are passed into CONSUME
  - Season - 'spring', 'summer', 'fall', 'winter'
  - 1000hr moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'
  - Duff moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'
  - Litter moisture level - 'very dry', 'dry', 'moderate', 'moist', 'wet', 'very wet'

  That makes a total of num_groups * 2 * 2 * 3 * 4 * 6 * 6 * 6 = 3,525,120 combinations,
  and that only considers one value for 'fuel_moisture_10hr_pct' (which is used
  for activity burns and is defaulted to 50).

 Each combination produces an output set that looks like the following:

  {'parameters': {'ecoregion': ['western'], 'season': ['spring'], 'area': array([1.]), 'fuelbeds': ['1'], 'can_con_pct': array([0.]), 'shrub_black_pct': array([50.]), 'pile_black_pct': array([0.]), 'fm_1000hr': array([10.]), 'fm_duff': array([20.]), 'fm_litter': array([4.]), 'filename': array(['FB_0001_FCCS.xml'], dtype=object), 'burn_type': ['natural'], 'units': ['tons_ac']}, 'heat release': {'flaming': array([1.2184763e+08]), 'smoldering': array([1.52693402e+08]), 'residual': array([94351858.62525254]), 'total': array([3.6889289e+08])}, 'consumption': {'summary': {'total': {'flaming': array([7.61547686]), 'smoldering': array([9.54333762]), 'residual': array([5.89699116]), 'total': array([23.05580564])}, 'canopy': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'shrub': {'flaming': array([1.27311208]), 'smoldering': array([0.1414569]), 'residual': array([0.]), 'total': array([1.41456898])}, 'nonwoody': {'flaming': array([0.166932]), 'smoldering': array([0.018548]), 'residual': array([0.]), 'total': array([0.18548])}, 'litter-lichen-moss': {'flaming': array([0.92454395]), 'smoldering': array([0.09209701]), 'residual': array([0.]), 'total': array([1.01664097])}, 'ground fuels': {'flaming': array([0.94656]), 'smoldering': array([6.62592]), 'residual': array([1.89312]), 'total': array([9.4656])}, 'woody fuels': {'flaming': array([4.30432882]), 'smoldering': array([2.66531571]), 'residual': array([4.00387116]), 'total': array([10.9735157])}}, 'canopy': {'overstory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'midstory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'understory': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 foliage': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 wood': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 1 no foliage': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 2': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'snags class 3': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'ladder fuels': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'shrub': {'primary live': {'flaming': array([1.27311208]), 'smoldering': array([0.1414569]), 'residual': array([0.]), 'total': array([1.41456898])}, 'secondary live': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'nonwoody': {'primary live': {'flaming': array([0.166932]), 'smoldering': array([0.018548]), 'residual': array([0.]), 'total': array([0.18548])}, 'secondary live': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'litter-lichen-moss': {'litter': {'flaming': array([0.74276937]), 'smoldering': array([0.08252993]), 'residual': array([0.]), 'total': array([0.8252993])}, 'lichen': {'flaming': array([0.00150227]), 'smoldering': array([7.9066804e-05]), 'residual': array([0.]), 'total': array([0.00158134])}, 'moss': {'flaming': array([0.18027231]), 'smoldering': array([0.00948802]), 'residual': array([0.]), 'total': array([0.18976033])}}, 'ground fuels': {'duff upper': {'flaming': array([0.94656]), 'smoldering': array([6.62592]), 'residual': array([1.89312]), 'total': array([9.4656])}, 'duff lower': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'basal accumulations': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'squirrel middens': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}}, 'woody fuels': {'piles': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'stumps sound': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, 'stumps rotten': {'flaming': array([0.00147025]), 'smoldering': array([0.00441075]), 'residual': array([0.0088215]), 'total': array([0.0147025])}, 'stumps lightered': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, '1-hr fuels': {'flaming': array([0.160911]), 'smoldering': array([0.008469]), 'residual': array([0.]), 'total': array([0.16938])}, '10-hr fuels': {'flaming': array([0.609768]), 'smoldering': array([0.067752]), 'residual': array([0.]), 'total': array([0.67752])}, '100-hr fuels': {'flaming': array([2.1202825]), 'smoldering': array([0.249445]), 'residual': array([0.1247225]), 'total': array([2.49445])}, '1000-hr fuels sound': {'flaming': array([0.3]), 'smoldering': array([0.15]), 'residual': array([0.05]), 'total': array([0.5])}, '1000-hr fuels rotten': {'flaming': array([0.50030151]), 'smoldering': array([0.75045226]), 'residual': array([1.25075377]), 'total': array([2.50150754])}, '10000-hr fuels sound': {'flaming': array([0.2]), 'smoldering': array([0.2]), 'residual': array([0.1]), 'total': array([0.5])}, '10000-hr fuels rotten': {'flaming': array([0.23418368]), 'smoldering': array([0.70255105]), 'residual': array([1.4051021]), 'total': array([2.34183684])}, '10k+-hr fuels sound': {'flaming': array([0.]), 'smoldering': array([0.]), 'residual': array([0.]), 'total': array([0.])}, '10k+-hr fuels rotten': {'flaming': array([0.17741188]), 'smoldering': array([0.53223565]), 'residual': array([1.06447129]), 'total': array([1.77411882])}}}}

"""

# TODO: Get appropriate groupings. For the sake of developing the script
#   we'll create two arbitrary groups

FCCS_GROUPS = {
    "group-0": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "gorup-21": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34, 36, 37, 38, 39, 40],
    "gorup-41": [41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59],
    "gorup-60": [60, 61, 62, 63, 65, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79],
    "gorup-80": [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 97, 98],
    "gorup-99": [99, 100, 101, 102, 103, 104, 105, 106, 107, 109, 110, 114, 115, 120, 121],
    "gorup-123": [123, 124, 125, 129, 131, 133, 134, 135, 138, 140, 142, 143, 146, 147, 148],
    "gorup-152": [152, 154, 155, 156, 157, 158, 161, 162, 164, 165, 166, 168, 170, 173, 174],
    "gorup-175": [175, 176, 178, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191],
    "gorup-196": [196, 203, 208, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221],
    "gorup-222": [222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236],
    "gorup-237": [237, 238, 239, 240, 241, 242, 243, 260, 261, 262, 263, 264, 265, 266, 267],
    "gorup-268": [268, 269, 270, 272, 273, 274, 275, 276, 279, 280, 281, 282, 283, 284, 286],
    "gorup-287": [287, 288, 289, 291, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311],
    "group-312": [312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326],
    "group-327": [327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 401, 402],
    "group-403": [403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417],
    "group-418": [418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432],
    "group-433": [433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 445, 448, 449, 450],
    "group-451": [451, 453, 454, 455, 456, 457, 458, 1201, 1202, 1203, 1205, 1223, 1225],
    "group-1241": [1241, 1242, 1243, 1244, 1245, 1247, 1252, 1260, 1261, 1262, 1271, 1273],
    "group-1280": [1280, 1281, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299],
}
for g in FCCS_GROUPS:
    FCCS_GROUPS[g] = [str(fccs_id) for fccs_id in FCCS_GROUPS[g]]

FCCS_ID_TO_GROUP = {f: g for g in FCCS_GROUPS for f in FCCS_GROUPS[g] }

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

def create_key(fccs_group, thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    return KEY_JOIN_CHAR.join([
        fccs_group, thousand_hr_fm_level, duff_fm_level, litter_fm_level
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
            items.append((new_key, v[0]))
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

def run_consume(fire_type, burn_type, season, fccs_group,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    # It may be more efficient to create one FuelConsumption
    # object for all runs, but it's safer to start with a clean
    # slate for each run
    fc = consume.FuelConsumption()
    fc.burn_type = burn_type

    fccs_id = FCCS_GROUPS[fccs_group][0]

    # TODO: get ecoregion from FCCS Id from consume's fuel loadings file
    fc.fuelbed_ecoregion = ECO_REGION_BY_FCCS_ID[fccs_id]
    fc.season = [season]
    fc.fuelbed_area_acres = [1]

    #fb['fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)

    # TODO: pick the most representative FCCS Id
    #    (for now we're just using the first)
    fc.fuelbed_fccs_ids = [fccs_id]

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
        SEASONS[0], list(FCCS_GROUPS)[0],
        list(FM_INPUT_VALS['fuel_moisture_1000hr_pct'])[0],
        list(FM_INPUT_VALS['fuel_moisture_duff_pct'])[0],
        list(FM_INPUT_VALS['fuel_moisture_litter_pct'])[0])

    flat_cons = nested_to_flat(nested_results['consumption'])

    flat_heat = nested_to_flat(nested_results['heat release'])


    return ['key'] + list(flat_cons), ['key'] + list(flat_heat)

def precompute_file(fire_type, burn_type, season, cons_fieldnames, heat_fieldnames):
    cons_filename = get_consumption_data_filename(fire_type, burn_type, season)
    heat_filename = get_heat_data_filename(fire_type, burn_type, season)

    with open(cons_filename, 'w') as cons_csvfile:
        with open(heat_filename, 'w') as heat_csvfile:
            # run consume once to get field names
            cons_writer = csv.DictWriter(cons_csvfile, fieldnames=cons_fieldnames)
            cons_writer.writeheader()

            heat_writer = csv.DictWriter(heat_csvfile, fieldnames=heat_fieldnames)
            heat_writer.writeheader()

            for fccs_group in FCCS_GROUPS:
                for thousand_hr_fm_level in FM_INPUT_VALS['fuel_moisture_1000hr_pct']:
                    for duff_fm_level in FM_INPUT_VALS['fuel_moisture_duff_pct']:
                        for litter_fm_level in FM_INPUT_VALS['fuel_moisture_litter_pct']:
                            nested_results = run_consume(fire_type,
                                burn_type, season,
                                fccs_group, thousand_hr_fm_level,
                                duff_fm_level, litter_fm_level)
                            key = create_key(fccs_group, thousand_hr_fm_level,
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
                precompute_file(fire_type, burn_type,
                    season, cons_fieldnames, heat_fieldnames)


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

    if fccs_id not in FCCS_ID_TO_GROUP:
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

    fccs_group = FCCS_ID_TO_GROUP[fccs_id]
    key = create_key(fccs_group, thousand_hr_fm_level,
        duff_fm_level, litter_fm_level)

    return ConsumeLookup(fire_type, burn_type, season).get(key)
