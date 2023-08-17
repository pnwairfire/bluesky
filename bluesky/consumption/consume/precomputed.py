"""bluesky.consumption.consume.precomputed
"""

import csv
import logging
import os

import consume
import numpy

from .consumeutils import FuelLoadingsManager

__all__ = [
    'FCCS_GROUPS',
    'FIRE_TYPES',
    'BURN_TYPES',
    'ECOREGIONS',
    'SEASONS',
    'ACTIVITY_SETTINGS',
    # 'VARIABLE_ACTIVITY_SETTINGS',
    'OTHER_SETTINGS',
    'VARIABLE_SETTINGS',
    'precompute',
]


##
## Params
##

"""
We pre-compute CONSUME for every combination of the following parameters
  - FCCS Group
  - Fire type - 'rx', 'wf' (which determines values for
    'canopy_consumption_pct', 'shrub_blackened_pct', 'pile_blackened_pct',
    'duff_pct_available', 'sound_cwd_pct_available', and 'rotten_cwd_pct_available'
  - Burn (fire) type - 'natural', 'activity' (which determines
    which input fields are passed into CONSUME
  - Ecoregion - "western", "southern", "boreal"
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
    "group-1" : [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34, 36, 37, 38, 39, 40,
        41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59,
        60, 61, 62, 63, 65, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
        80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 97, 98,
        99, 100, 101, 102, 103, 104, 105, 106, 107, 109, 110, 114, 115, 120, 121,
        123, 124, 125, 129, 131, 133, 134, 135, 138, 140, 142, 143, 146, 147, 148,
        152, 154, 155, 156, 157, 158, 161, 162, 164, 165, 166, 168, 170, 173, 174,
        175, 176, 178, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191,
        196, 203, 208, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221,
        222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236,
        237, 238, 239, 240, 241, 242, 243, 260, 261, 262, 263, 264, 265, 266, 267,
        268, 269, 270, 272, 273, 274, 275, 276, 279, 280, 281, 282, 283, 284, 286,
        287, 288, 289, 291
    ],
    "group-2": [
        301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311,
        312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326,
        327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 401, 402,
        403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417,
        418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432,
        433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 445, 448, 449, 450,
        451, 453, 454, 455, 456, 457, 458, 1201, 1202, 1203, 1205, 1223, 1225,
        1241, 1242, 1243, 1244, 1245, 1247, 1252, 1260, 1261, 1262, 1271, 1273,
        1280, 1281, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299,
    ]
}
FCCS_ID_TO_GROUP = {str(f): g for g in FCCS_GROUPS for f in FCCS_GROUPS[g] }

FIRE_TYPES = ['rx', 'wf']
BURN_TYPES = ['natural', 'activity'] # a.k.a. 'fuel_type'
ECOREGIONS =  ["western", "southern", "boreal"]
SEASONS = ['spring', 'summer', 'fall', 'winter']

# Activity settings are the same for rx and wf
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
    'canopy_consumption_pct': {'rx': 0, 'wf': 0},
    'shrub_blackened_pct': {'rx': 50, 'wf': 50},
    'pile_blackened_pct': {'rx': 0, 'wf': 0},
    'duff_pct_available': {'rx': 5, 'wf': 10},
    'sound_cwd_pct_available': {'rx': 5, 'wf': 10},
    'rotten_cwd_pct_available': {'rx': 5, 'wf': 10}
}

VARIABLE_SETTINGS = {
    'fuel_moisture_1000hr_pct': {  # normal defualts: {'rx': 35, 'wf': 15},
        'very dry': 10,
        'dry': 15,
        'moderate': 30,
        'moist': 35,
        'wet': 40,
        'very wet': 60
    },
    'fuel_moisture_duff_pct': {  # normal defualts: {'rx': 100, 'wf': 40},
        'very dry': 20,
        'dry': 40,
        'moderate': 75,
        'moist': 100,
        'wet': 130,
        'very wet': 180
    },
    'fuel_moisture_litter_pct': {  # normal defualts: {'rx': 22, 'wf': 10},
        'very dry': 4,
        'dry': 10,
        'moderate': 16,
        'moist': 22,
        'wet': 30,
        'very wet': 40
    },
}

##
## Methods used during pre-computation and look-up
##

KEY_JOIN_CHAR = ';'

def create_key(fire_type, burn_type, ecoregion, season, fccs_group,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    return KEY_JOIN_CHAR.join([fire_type, burn_type, ecoregion, season, fccs_group,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level])

HEADER_JOIN_CHAR = ';'

def flatten_consumption_dict(nested_cons):
    """Flattens the consumption dict and converts numpy.ndarray values to scalars
    """
    d = {}
    for c in nested_cons['consumption']: # fuel catefory (e.g. 'shrub')
        for fc in nested_cons['consumption'][c]: # fuel sub-category (e.g. 'primary live')
            for p in nested_cons['consumption'][c][fc]: # phase (e.g. 'flaming')
                d[HEADER_JOIN_CHAR.join([c,fc,p])] = nested_cons['consumption'][c][fc][p][0]
    return d

def nest_consumption_dict(flat_cons):
    """Reconstitutes nested dict structure with numpy.ndarray values, as
    originally returned by consume
    """
    nested_cons = {}
    for k in flat_cons:
        keys = k.split(HEADER_JOIN_CHAR)
        d = nested_cons
        prev = None
        for f in keys:
            d[f] = {} if f not in d else d[f]
            prev = d
            d = d[f]
        prev[f] = numpy.array(flat_cons[k])

    return nested_cons

def get_data_filename():
    return os.path.join(os.path.dirname(__file__), 'data', 'precomputed.csv')


##
## Generation of data
##

def run_consume(fire_type, burn_type, ecoregion, season, fccs_group,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    # It may be more efficient to create one FuelConsumption
    # object for all runs, but it's safer to start with a clean
    # slate for each run
    fc = consume.FuelConsumption()
    fc.burn_type = burn_type
    fc.fuelbed_ecoregion = [ecoregion]
    fc.season = [season]
    fc.fuelbed_area_acres = [1]

    #fb['fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)

    # TODO: pick the most representative FCCS Id
    #    (for now we're just using the first)
    fc.fuelbed_fccs_ids = [FCCS_GROUPS[fccs_group][0]]

    if burn_type == 'activity':
        for k, v in ACTIVITY_SETTINGS.items():
            setattr(fc, k, v)

    for k, vDict in OTHER_SETTINGS.items():
        logging.warn("Setting %s to %s", k, vDict[fire_type])
        try:
            setattr(fc, k, vDict[fire_type])
        except Exception as e:
            # TODO: figure out why we're failing to set some inputs
            logging.warn("Failed to set %s", k)

    fc.fuel_moisture_1000hr_pct = VARIABLE_SETTINGS['fuel_moisture_1000hr_pct'][thousand_hr_fm_level]
    fc.fuel_moisture_duff_pct = VARIABLE_SETTINGS['fuel_moisture_duff_pct'][duff_fm_level]
    fc.fuel_moisture_litter_pct = VARIABLE_SETTINGS['fuel_moisture_litter_pct'][litter_fm_level]

    return fc.results()

def precompute():
    #fuel_loadings_manager = FuelLoadingsManager()

    # We'll instantiate once we have fiel

    with open(get_data_filename(), 'w') as csvfile:
        # run consume once to get field names
        nested_cons = run_consume(FIRE_TYPES[0], BURN_TYPES[0], ECOREGIONS[0],
            SEASONS[0], list(FCCS_GROUPS)[0],
            list(VARIABLE_SETTINGS['fuel_moisture_1000hr_pct'])[0],
            list(VARIABLE_SETTINGS['fuel_moisture_duff_pct'])[0],
            list(VARIABLE_SETTINGS['fuel_moisture_litter_pct'])[0])
        flat_cons = flatten_consumption_dict(nested_cons)
        fieldnames = ['key'] + list(flat_cons)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for fire_type in FIRE_TYPES:
            for burn_type in BURN_TYPES:
                for ecoregion in ECOREGIONS:
                    for season in SEASONS:
                        for fccs_group in FCCS_GROUPS:
                            for thousand_hr_fm_level in VARIABLE_SETTINGS['fuel_moisture_1000hr_pct']:
                                for duff_fm_level in VARIABLE_SETTINGS['fuel_moisture_duff_pct']:
                                    for litter_fm_level in VARIABLE_SETTINGS['fuel_moisture_litter_pct']:
                                        nested_cons = run_consume(fire_type,
                                            burn_type, ecoregion, season,
                                            fccs_group, thousand_hr_fm_level,
                                            duff_fm_level, litter_fm_level)
                                        flat_cons = flatten_consumption_dict(nested_cons)
                                        flat_cons['key'] = create_key(fire_type,
                                            burn_type, ecoregion, season,
                                            fccs_group, thousand_hr_fm_level,
                                            duff_fm_level, litter_fm_level)
                                        writer.writerow(flat_cons)


##
## Reading
##


class ConsumeLookup(object):
    """Class for managing bluesky configuration.

    This is a Singleton, so that data are loaded only once
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConsumeLookup, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, '_data'):
            self._load()

    def _load(self):
        self._data = {}
        logging.info("Loading pre-computed CONSUME data")
        with open(get_data_filename()) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.pop('key')
                self._data[key] = nest_consumption_dict(row)
        logging.info("Finished loading pre-computed CONSUME data")

    def get(self, key):
        return self._data[key]


def look_up(fccs_id, fire_type, burn_type, ecoregion, season,
        thousand_hr_fm_level, duff_fm_level, litter_fm_level):
    # TODO:
    #  - use Singleton lookup object
    #  - determine FM categories
    #  - create key from parameters
    #  - look up data using key
    #  - unflatten dict
    #  - convert scalar vals to arrays (to match consumption output)

    if fccs_id not in FCCS_ID_TO_GROUP:
        raise RuntimeError(f"Invalid FCCS Id {fccs_id}")

    fccs_group = FCCS_ID_TO_GROUP[fccs_id]
    key = create_key(
        fire_type.lower(),
        burn_type.lower(),
        ecoregion.lower(),
        season.lower(),
        fccs_group,
        thousand_hr_fm_level.lower(),
        duff_fm_level.lower(),
        litter_fm_level.lower()
    )

    return ConsumeLookup().get(key)
