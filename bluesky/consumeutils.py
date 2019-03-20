"""bluesky.consumeutils

TODO: move this (and other top level utility modules?) into nested package ?
"""

__author__ = "Joel Dubowy"

import copy
import tempfile

#import numpy
import consume

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    "_apply_settings",
    "FuelLoadingsManager",
    "FuelConsumptionForEmissions"
]

# TODO: These burn-type pecific settings sets might not be correct
# TODO: Check with Susan P, Susan O, Kjell, etc. to make sure defaults are correct
# TODO: Check with Susan P, Susan O, Kjell, etc. to make sure sysnonyms are
#  valid and to see if any are missing
SETTINGS = {
    'natural': [],
    'activity': [
        {
            'field': 'slope',
            'default': 5 # percent, from 1 to 100; default from consume package
        },
        {
            'field': 'windspeed',
            'default': 5,  # default from consume package
            # TODO: is 'max_wind' a valid synonym? or 'min_wind_aloft'?
        },
        {
            'field': 'days_since_rain',
            'default': 10,   # our default
            'synonyms': ['rain_days'] # TODO: confirm
        },
        {
            'field': 'fuel_moisture_10hr_pct',
            'default': 50, # default from consume package
            'synonyms': ['moisture_10hr'] # TODO: confirm
        },
        {
            'field': 'length_of_ignition',
            'default': 120 # in minutes; our default
        },
        {
            'field': 'fm_type',
            'default': "MEAS-Th" # default from consume package
        }
    ],
    'all': [
        {
            'field': 'fuel_moisture_1000hr_pct',
            'default': 50, # default from consume package
            'synonyms': ['moisture_1khr'] # TODO: confirm
        },
        {
            'field': 'fuel_moisture_duff_pct',
            'default': 50, # default from consume package
            'synonyms': ['moisture_duff'] # TODO: confirm
        },
        {
            'field': 'fuel_moisture_litter_pct',
            'default': 50, # TODO: confirm
            'synonyms': ['moisture_litter'] # TODO: confirm
        },
        {
            'field': 'canopy_consumption_pct',
            'default': 0,
            # TDOO: is 'canopy' a valid synonym
        },
        {
            'field': 'shrub_blackened_pct',
            'default': 50,
            # TODO: is 'shrub' a valid synonym
        },
        {
            'field': 'output_units',
            'default': "tons_ac"  # default in consume package is 'tons_ac'
        },
        {
            'field': 'pile_blackened_pct',
            'default': 0
        },
    ]
}
def _apply_settings(fc, location, burn_type):
    valid_settings = SETTINGS[burn_type] + SETTINGS['all']
    for d in valid_settings:
        possible_name = [d['field']] + d.get('synonyms', [])
        defined_fields = [f for f in possible_name if f in location]
        if defined_fields:
            # use first of defined fields - it's not likely that
            # len(defined_fields) > 1
            setattr(fc, d['field'], location[defined_fields[0]])
        elif 'default' in d:
            setattr(fc, d['field'], d['default'])
        else:
            raise BlueSkyConfigurationError("Specify {} for {} burns".format(
                d['field'], burn_type))

class FuelLoadingsManager(object):

    FUEL_LOADINGS_KEY_MAPPINGS = {
        "bas_loading": "basal_accum_loading",
        "cover_type": "cover_type",
        "duff_lower_depth": "duff_lower_depth",
        "duff_lower_loading": "duff_lower_loading",
        "duff_upper_depth": "duff_upper_depth",
        "duff_upper_loading": "duff_upper_loading",
        "ecoregion": "ecoregion",
        "efg_activity": "efg_activity",
        "efg_natural": "efg_natural",
        "filename": "filename",
        "ladder": "ladderfuels_loading",
        "lch_depth": "lichen_depth",
        "lichen_loading": "lichen_loading",
        "lit_depth": "litter_depth",
        "litter_loading": "litter_loading",
        "midstory": "midstory_loading",
        "moss_depth": "moss_depth",
        "moss_loading": "moss_loading",
        "nw_prim": "nw_primary_loading",
        "nw_prim_pctlv": "nw_primary_perc_live",
        "nw_seco": "nw_secondary_loading",
        "nw_seco_pctlv": "nw_secondary_perc_live",
        "overstory": "overstory_loading",
        "pile_clean_loading": "pile_clean_loading",
        "pile_dirty_loading": "pile_dirty_loading",
        "pile_vdirty_loading": "pile_vdirty_loading",
        "shrub_prim": "shrubs_primary_loading",
        "shrub_prim_pctlv": "shrubs_primary_perc_live",
        "shrub_seco": "shrubs_secondary_loading",
        "shrub_seco_pctlv": "shrubs_secondary_perc_live",
        "snag1f": "snags_c1_foliage_loading",
        "snag1w": "snags_c1_wood_loading",
        "snag1nf": "snags_c1wo_foliage_loading",
        "snag2": "snags_c2_loading",
        "snag3": "snags_c3_loading",
        "sqm_loading": "squirrel_midden_loading",
        "Total_available_fuel_loading": "total_available_fuel_loading",
        "understory": "understory_loading",
        "oneK_hr_rotten": "w_rotten_3_9_loading",
        "tenK_hr_rotten": "w_rotten_9_20_loading",
        "tnkp_hr_rotten": "w_rotten_gt20_loading",
        "one_hr_sound": "w_sound_0_quarter_loading",
        "hun_hr_sound": "w_sound_1_3_loading",
        "oneK_hr_sound": "w_sound_3_9_loading",
        "tenK_hr_sound": "w_sound_9_20_loading",
        "tnkp_hr_sound": "w_sound_gt20_loading",
        "ten_hr_sound": "w_sound_quarter_1_loading",
        "stump_lightered": "w_stump_lightered_loading",
        "stump_rotten": "w_stump_rotten_loading",
        "stump_sound": "w_stump_sound_loading"
    }

    NON_LOADINGS_FIELDS = [
        'filename','cover_type','ecoregion','efg_natural','efg_activity'
    ]

    # Note: It's important that there are no leading spaces before the
    # header or before the fuels row.  They break consume.
    FCCS_LOADINGS_CSV_HEADER = """GeneratorName=FCCS 3.0,GeneratorVersion=3.0.0,DateCreated=11/14/2014
fuelbed_number,filename,cover_type,ecoregion,overstory_loading,midstory_loading,understory_loading,snags_c1_foliage_loading,snags_c1wo_foliage_loading,snags_c1_wood_loading,snags_c2_loading,snags_c3_loading,shrubs_primary_loading,shrubs_secondary_loading,shrubs_primary_perc_live,shrubs_secondary_perc_live,nw_primary_loading,nw_secondary_loading,nw_primary_perc_live,nw_secondary_perc_live,w_sound_0_quarter_loading,w_sound_quarter_1_loading,w_sound_1_3_loading,w_sound_3_9_loading,w_sound_9_20_loading,w_sound_gt20_loading,w_rotten_3_9_loading,w_rotten_9_20_loading,w_rotten_gt20_loading,w_stump_sound_loading,w_stump_rotten_loading,w_stump_lightered_loading,litter_depth,litter_loading,lichen_depth,lichen_loading,moss_depth,moss_loading,basal_accum_loading,squirrel_midden_loading,ladderfuels_loading,duff_lower_depth,duff_lower_loading,duff_upper_depth,duff_upper_loading,pile_clean_loading,pile_dirty_loading,pile_vdirty_loading,Total_available_fuel_loading,efg_natural,efg_activity
"""
    FCCS_LOADINGS_CSV_ROW_TEMPLATE = """{fuelbed_number},{filename},{cover_type},{ecoregion},{overstory_loading},{midstory_loading},{understory_loading},{snags_c1_foliage_loading},{snags_c1wo_foliage_loading},{snags_c1_wood_loading},{snags_c2_loading},{snags_c3_loading},{shrubs_primary_loading},{shrubs_secondary_loading},{shrubs_primary_perc_live},{shrubs_secondary_perc_live},{nw_primary_loading},{nw_secondary_loading},{nw_primary_perc_live},{nw_secondary_perc_live},{w_sound_0_quarter_loading},{w_sound_quarter_1_loading},{w_sound_1_3_loading},{w_sound_3_9_loading},{w_sound_9_20_loading},{w_sound_gt20_loading},{w_rotten_3_9_loading},{w_rotten_9_20_loading},{w_rotten_gt20_loading},{w_stump_sound_loading},{w_stump_rotten_loading},{w_stump_lightered_loading},{litter_depth},{litter_loading},{lichen_depth},{lichen_loading},{moss_depth},{moss_loading},{basal_accum_loading},{squirrel_midden_loading},{ladderfuels_loading},{duff_lower_depth},{duff_lower_loading},{duff_upper_depth},{duff_upper_loading},{pile_clean_loading},{pile_dirty_loading},{pile_vdirty_loading},{total_available_fuel_loading},{efg_natural},{efg_activity}
"""

    def __init__(self, all_fuel_loadings={}):
        # convert all keys to lowercase (e.g. in case
        # 'Total_available_fuel_loading' is used instead of
        # 'total_available_fuel_loading')
        self._all_fuel_loadings = {}
        if all_fuel_loadings:
            for fccs_id, loadings in all_fuel_loadings.items():
                self._all_fuel_loadings[fccs_id] = {k.lower(): v for k, v in loadings.items()}

        self._default_fuel_loadings = {}
        self._default_fccsdb_obj = None # lazy instantiate
        self._custom = {}

    ##
    ## Public Interface
    ##

    def get_fuel_loadings(self, fccs_id, fccsdb_obj=None):
        # TODO: make sure this method works both when default fuel loadings
        # are used and when custom ones are used

        if not fccsdb_obj:
            if fccs_id not in self._default_fuel_loadings:
                # instantiate default fccsdb obj if not yet done
                if not self._default_fccsdb_obj:
                    self._default_fccsdb_obj = consume.fccs_db.FCCSDB()
                self._default_fuel_loadings[fccs_id] = self._get_fuel_loadings_from_fccsdb_obj(
                    fccs_id, self._default_fccsdb_obj)
            return self._default_fuel_loadings[fccs_id]

        return self._get_fuel_loadings_from_fccsdb_obj(fccs_id, fccsdb_obj)

    def generate_custom_csv(self, fccs_id):
        fccs_id = str(fccs_id)  # shouldn't be necessary, but just in case...

        if not self._all_fuel_loadings or not self._all_fuel_loadings.get(fccs_id):
            # To indicate that consume's built-in fuel loadings should be used,
            # consume.FuelConsumption must be instantiated with fccs_file=""
            return ""

        # TODO: wrap self._generate(fccs_id) in try/except, and return
        #   empty string on failure?  (maybe not, since we might not want
        #   to silently use default fuel_loadings when alternate is specified)
        return self._generate(fccs_id)

    ##
    ## Helper Methods
    ##


    def _get_fuel_loadings_from_fccsdb_obj(self, fccs_id, fccsdb_obj):
        # iterate through the rows in the fccsdb_obj.loadings_data_
        # pandas.DataFrame until you find row with fuel loadings for fccs_id
        for i in range(len(fccsdb_obj.loadings_data_)):
            row = fccsdb_obj.loadings_data_.irow(i)
            if row[0] == str(fccs_id):
                d = dict(row)
                for k in d:
                    if k in self.FUEL_LOADINGS_KEY_MAPPINGS:
                        d[self.FUEL_LOADINGS_KEY_MAPPINGS[k]] = d.pop(k)
                d.pop('fccs_id', None)
                return d


    def _fill_in_defaults(self, fuel_loadings):
        based_on_fccs_id = fuel_loadings.pop('based_on_fccs_id', None)
        if based_on_fccs_id:
            based_on_fccs_id = str(based_on_fccs_id)
            if based_on_fccs_id == fuel_loadings['fuelbed_number']:
                raise ValueError("Custom fuel bed can't have same id as the "
                    "one on which it's based.")
            # calling self.get_fuel_loadings without passing fccsdb obj
            # returns defaults
            defaults = self.get_fuel_loadings(based_on_fccs_id)
            for k in defaults:
                if k not in fuel_loadings:
                    fuel_loadings[k] = defaults[k]

    def _generate(self, fccs_id):
        if fccs_id not in self._custom:
            fuel_loadings = copy.copy(self._all_fuel_loadings[fccs_id])

            f = tempfile.NamedTemporaryFile(mode='w')

            f.write(self.FCCS_LOADINGS_CSV_HEADER)
            # set fuelbed_id
            fuel_loadings['fuelbed_number'] = fccs_id
            # default non-loadings columns to empty string
            for k in self.NON_LOADINGS_FIELDS:
                fuel_loadings[k] = fuel_loadings.get(k, "")

            self._fill_in_defaults(fuel_loadings)

            # Keep the try/except in case based_on_fccs_id isn't defined and defaults
            # aren't filled in.
            try:
                row = self.FCCS_LOADINGS_CSV_ROW_TEMPLATE.format(**fuel_loadings)
            except KeyError as e:
                raise BlueSkyConfigurationError(
                    "Missing fuel loadings field: '{}'".format(str(e)))

            f.write(row)
            f.flush()

            # return temp file object, not just it's name, since file is
            # deleted once obejct goes out of scope
            self._custom[fccs_id] = f

        return self._custom[fccs_id].name


# consume internall stores consumption data in arrays; order matters
CONSUME_FUEL_CATEGORIES = {
    'summary' : [
        'total', 'canopy', 'shrub', 'nonwoody', 'litter-lichen-moss',
        'ground fuels', 'woody fuels'
    ],
    'canopy' : [
        'overstory', 'midstory', 'understory', 'snags class 1 foliage',
        'snags class 1 wood', 'snags class 1 no foliage', 'snags class 2',
        'snags class 3', 'ladder fuels'
    ],
    'shrub': [
        'primary live', 'primary dead', 'secondary live', 'secondary dead'
    ],
    'nonwoody': [
        'primary live', 'primary dead', 'secondary live', 'secondary dead'
    ],
    'litter-lichen-moss': [
        'litter', 'lichen', 'moss'
    ],
    'ground fuels': [
        'duff upper', 'duff lower', 'basal accumulations', 'squirrel middens'
    ],
    'woody fuels': [
        'piles', 'stumps sound', 'stumps rotten', 'stumps lightered',
        '1-hr fuels', '10-hr fuels', '100-hr fuels', '1000-hr fuels sound',
        '1000-hr fuels rotten', '10000-hr fuels sound',
        '10000-hr fuels rotten', '10k+-hr fuels sound', '10k+-hr fuels rotten'
    ]
}

CONSUME_FIELDS = ["flaming", "smoldering", "residual", "total"]

class FuelConsumptionForEmissions(consume.FuelConsumption):
    def __init__(self, consumption_data, heat_data, area, burn_type, fccs_id,
            location, fccs_file=None):
        fccs_file = fccs_file or ""
        super(FuelConsumptionForEmissions, self).__init__(fccs_file=fccs_file)

        # TODO:  figure out how to avoid re-computing consumption and still
        #  compute emissions correctly; for now, let it recompute, since
        #  consumption was most likely produced with consume using the same
        #  conifguration as this emissions run (which means this is wasted
        #  computation, but shouldn't be changing the consumption values)

        # self._set_consumption_data(consumption_data)
        # self._set_heat_data(heat_data)
        self.burn_type = burn_type
        self.fuelbed_fccs_ids = [fccs_id]
        self.fuelbed_area_acres = [area]
        self.fuelbed_ecoregion = [location['ecoregion']]

        _apply_settings(self, location, burn_type)

    # def _calculate(self):
    #     """Overrides consume.FuelConsumption._calculate so that it doesn't
    #     recalculate _cons_data and _heat_data when it's called by
    #     consume.Emissions._calculate

    #     Note:  We could have _calculate skipped altogether by setting
    #         consume.Emissions._have_cons_data = len(
    #             FuelConsumptionForEmissions._cons_data[0][0])
    #     but we need calcualte to be called in order to set self._cons_data_piles
    #     """
    #     loadings = self._get_loadings_for_specified_files(
    #         self._settings.get('fuelbeds'))

    #     self._cons_data_piles = consume.con_calc_natural.ccon_piles(
    #         self._settings.get('pile_black_pct'), loadings)

    # def _set_consumption_data(self, consumption_data):
    #     # This is a reverse of what's done in
    #     #  consume.FuelConsumption.make_dictionary_of_lists
    #     cons_data = []
    #     for c, subc in CONSUME_FUEL_CATEGORIES.items():
    #         for sc in subc:
    #             cons_data.append([
    #                 # TODO: use get's and default missing values to 0
    #                 consumption_data[c][sc][f] for f in CONSUME_FIELDS
    #             ])
    #     self._cons_data = numpy.array(cons_data)

    # def _set_heat_data(self, heat_data):
    #     # _heat_data is indeed supposed to be an array with a single nested array
    #     self._heat_data = numpy.array([[heat_data[f] for f in CONSUME_FIELDS]])
