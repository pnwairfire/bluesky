"""bluesky.consumeutils

TODO: move this (and other top level utility modules?) into nested package ?
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2016, AirFire, PNW, USFS"

import copy
import tempfile

from bluesky.exceptions import BlueSkyConfigurationError

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
def _apply_settings(fc, fire, burn_type):
    valid_settings = SETTINGS[burn_type] + SETTINGS['all']
    for k, default in valid_settings:
        if fire.location.has_key(k):
            setattr(fc, k, fire.location[k])
        elif default is not None:
            setattr(fc, k, default)

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
        self._all_fuel_loadings = all_fuel_loadings
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
                    if self.FUEL_LOADINGS_KEY_MAPPINGS.has_key(k):
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

            f = tempfile.NamedTemporaryFile()

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
            except KeyError, e:
                raise BlueSkyConfigurationError(
                    "Missing fuel loadings field: '{}'".format(e.message))

            f.write(row)
            f.flush()

            # return temp file object, not just it's name, since file is
            # deleted once obejct goes out of scope
            self._custom[fccs_id] = f

        return self._custom[fccs_id].name