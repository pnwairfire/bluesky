"""bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import abc
import copy
import itertools
import logging
import sys

from emitcalc import __version__ as emitcalc_version
from emitcalc.calculator import EmissionsCalculator
from eflookup import __version__ as eflookup_version
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

import consume

from bluesky import datautils, datetimeutils
from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.io import capture_stdout

from bluesky.consumeutils import (
    _apply_settings, FuelLoadingsManager, FuelConsumptionForEmissions,
    CONSUME_FIELDS, CONSUME_VERSION_STR
)

__all__ = [
    'run'
]
__version__ = "0.1.0"


def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object

    Config options:
     - emissions > model -- emissions model to use
     - emissions > species -- whitelist of species to compute emissions for
     - emissions > include_emissions_details -- whether or not to include
        emissions per fuel category per phase, as opposed to just per phase
     - emissions > fuel_loadings --
     - consumption > fuel_loadings -- considered if fuel loadings aren't
        specified in the emissions config
    """
    model = Config().get('emissions', 'model')

    include_emissions_details = Config().get(
        'emissions', 'include_emissions_details')
    fires_manager.processed(__name__, __version__, model=model,
        emitcalc_version=emitcalc_version, eflookup_version=eflookup_version,
        consume_version=CONSUME_VERSION_STR)

    try:
        klass_name = ''.join([e.capitalize() for e in model.split('-')])
        klass = getattr(sys.modules[__name__], klass_name)
        e = klass(fires_manager.fire_failure_handler)
    except AttributeError:
        msg = "Invalid emissions model: '{}'.".format(model)
        if model == 'urbanski':
            msg += " The urbanski model has be replaced by prichard-oneill"
        raise BlueSkyConfigurationError(msg)

    e.run(fires_manager.fires)

    # fix keys
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for aa in fire.active_areas:
                for loc in aa.locations:
                    for fb in loc['fuelbeds']:
                        _fix_keys(fb['emissions'])
                        if include_emissions_details:
                            _fix_keys(fb['emissions_details'])

    datautils.summarize_all_levels(fires_manager, 'emissions')
    if include_emissions_details:
        datautils.summarize_over_all_fires(fires_manager, 'emissions_details')


def _fix_keys(emissions):
    for k in emissions:
        # in case someone spcifies custom EF's with 'PM25'
        if k == 'PM25':
            emissions['PM2.5'] = emissions.pop('PM25')
        elif k == 'NMOC':
            # Total non-methane VOCs
            emissions['VOC'] = emissions.pop('NMOC')
        elif isinstance(emissions[k], dict):
            _fix_keys(emissions[k])


##
## Emissions base class
##

class EmissionsBase(object, metaclass=abc.ABCMeta):

    def __init__(self, fire_failure_handler):
        self.fire_failure_handler = fire_failure_handler
        self.include_emissions_details = Config().get(
            'emissions', 'include_emissions_details')
        self.species = Config().get('emissions', 'species')

    @abc.abstractmethod
    def run(self, fires):
        pass


##
## FEPS
##

class Feps(EmissionsBase):

    def __init__(self, fire_failure_handler):
        super(Feps, self).__init__(fire_failure_handler)

        # The same lookup object is used for both Rx and WF
        self.calculator = EmissionsCalculator(FepsEFLookup(),
            species=self.species)

    def run(self, fires):
        logging.info("Running emissions module FEPS EFs")

        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    CONVERSION_FACTOR = 0.0005 # 1.0 ton / 2000.0 lbs

    def _run_on_fire(self, fire):
        if 'activity' not in fire:
            raise ValueError(
                "Missing activity data required for computing emissions")
        for aa in fire.active_areas:
            for loc in aa.locations:
                if 'fuelbeds' not in loc:
                   raise ValueError(
                        "Missing fuelbed data required for computing emissions")
                for fb in loc['fuelbeds']:
                    if 'consumption' not in fb:
                        raise ValueError(
                            "Missing consumption data required for computing emissions")
                    _calculate(self.calculator, fb, self.include_emissions_details)
                    # TODO: Figure out if we should indeed convert from lbs to tons;
                    #   if so, uncomment the following
                    # Note: According to BSF, FEPS emissions are in lbs/ton consumed.  Since
                    # consumption is in tons, and since we want emissions in tons, we need
                    # to divide each value by 2000.0
                    # datautils.multiply_nested_data(fb['emissions'], self.CONVERSION_FACTOR)
                    # if self.include_emissions_details:
                    #     datautils.multiply_nested_data(fb['emissions_details'], self.CONVERSION_FACTOR)

##
## Prichard / O'Neill
##


class PrichardOneill(EmissionsBase):

    def __init__(self, fire_failure_handler):
        super(PrichardOneill, self).__init__(fire_failure_handler)

    def run(self, fires):
        logging.info("Running emissions module with Prichard / O'Neill EFs")

        # Instantiate two lookup object, one Rx and one WF, to be reused
        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    # Consumption values are in tons, Prichard/ONeill EFS are in g/kg, and
    # we want emissions values in tons.  Since 1 g/kg == 2 lbs/ton, we need
    # to multiple the emissions output by:
    #   (2 lbs/ton) * (1 ton / 2000lbs) = 1/1000 = 0.001
    CONVERSION_FACTOR = 0.001

    def _run_on_fire(self, fire):
        if 'activity' not in fire:
            raise ValueError(
                "Missing activity data required for computing emissions")

        for aa in fire.active_areas:
            for loc in aa.locations:
                if 'fuelbeds' not in loc:
                    raise ValueError(
                        "Missing fuelbed data required for computing emissions")
                for fb in loc['fuelbeds']:
                    if 'consumption' not in fb:
                        raise ValueError(
                            "Missing consumption data required for computing emissions")
                    if 'fccs_id' not in fb:
                        raise ValueError(
                            "Missing FCCS Id required for computing emissions")
                    fccs2ef = Fccs2Ef(fb["fccs_id"], is_rx=(fire["type"]=="rx"))
                    calculator = EmissionsCalculator(fccs2ef, species=self.species)
                    _calculate(calculator, fb, self.include_emissions_details)
                    # Convert from lbs to tons
                    # TODO: Update EFs to be tons/ton in a) eflookup package,
                    #   b) just after instantiating look-up objects, above,
                    #   or c) just before calling EmissionsCalculator, above
                    datautils.multiply_nested_data(fb['emissions'], self.CONVERSION_FACTOR)
                    if self.include_emissions_details:
                        datautils.multiply_nested_data(fb['emissions_details'], self.CONVERSION_FACTOR)

##
## CONSUME
##

class Consume(EmissionsBase):

    def __init__(self, fire_failure_handler):
        super(Consume, self).__init__(fire_failure_handler)

        self.species = self.species and [e.upper() for e in self.species]

        all_fuel_loadings = (Config().get('emissions','fuel_loadings')
            or Config().get('consumption','fuel_loadings'))
        self.fuel_loadings_manager = FuelLoadingsManager(
            all_fuel_loadings=all_fuel_loadings)


    def run(self, fires):
        logging.info("Running emissions module with CONSUME")

        # look for custom fuel loadings first in the emissions config and then
        # in the consumption config

        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    def _run_on_fire(self, fire):
        logging.debug("Consume emissions - fire {}".format(fire.get("id")))

        if 'activity' not in fire:
            raise ValueError(
                "Missing activity data required for computing consume emissions")

        burn_type = fire.get("fuel_type") or 'natural'
        # TODO: set burn type to 'activity' if fire["fuel_type"] == 'piles' ?
        if burn_type == 'piles':
            raise ValueError("Consume can't be used for fuel type 'piles'")

        for aa in fire.active_areas:
            season = datetimeutils.season_from_date(aa.get('start'))
            for loc in aa.locations:
                if 'fuelbeds' not in loc:
                    raise ValueError(
                        "Missing fuelbed data required for computing emissions")

                for fb in loc['fuelbeds']:
                    self._run_on_fuelbed(aa, loc, fb, season, burn_type)

    def _run_on_fuelbed(self, active_area, loc, fb, season, burn_type):
        if 'consumption' not in fb:
            raise ValueError(
                "Missing consumption data required for computing emissions")
        if 'heat' not in fb:
            raise ValueError(
                "Missing heat data required for computing emissions")
        if 'pct' not in fb:
            raise ValueError(
                "Missing fuelbed 'ptc' required for computing emissions")
        if 'ecoregion' not in active_area:
            raise ValueError(
                "Missing ecoregion required for computing emissions")

        fuel_loadings_csv_filename = self.fuel_loadings_manager.generate_custom_csv(
             fb['fccs_id'])
        # unlike with consume consumption results, emissions results reflect
        # how you set area and output_units
        area = (fb['pct'] / 100.0) * loc['area']
        fc = FuelConsumptionForEmissions(fb["consumption"], fb['heat'],
            area, burn_type, fb['fccs_id'], season, active_area,
            fccs_file=fuel_loadings_csv_filename)

        e_fuel_loadings = self.fuel_loadings_manager.get_fuel_loadings(
            fb['fccs_id'], fc.FCCS)
        fb['emissions_fuel_loadings'] = e_fuel_loadings
        e = consume.Emissions(fuel_consumption_object=fc)
        e.output_units = 'tons'

        # Consume emissions prints out lines like
        #    Converting units: tons_ac -> tons
        # which we want to capture and ignore
        # TODO: should we log??
        with capture_stdout() as stdout_buffer:
            r = e.results()['emissions']

        fb['emissions'] = {f: {} for f in CONSUME_FIELDS}
        # r's key hierarchy is species > phase; we want phase > species
        for k in r:
            upper_k = 'PM2.5' if k == 'pm25' else k.upper()
            if k != 'stratum' and (not self.species or upper_k in self.species):
                for p in r[k]:
                    fb['emissions'][p][upper_k] = r[k][p]

        if self.include_emissions_details:
            # Note: consume gives details per fuel category, not per
            #  subcategory; to match what FEPS and Prichard/O'Neill calculators
            #  produce, put all per-category details under'summary'
            # The details are under key 'stratum'. the key hierarchy is:
            #    'stratum' > species > fuel category > phase
            #   we want phase > species:
            #     'summary' > fuel category > phase > species
            fb['emissions_details'] = { "summary": {} }
            for k in r.get('stratum', {}):
                upper_k = 'PM2.5' if k == 'pm25' else k.upper()
                if not self.species or upper_k in self.species:
                    for c in r['stratum'][k]:
                        fb['emissions_details']['summary'][c] = fb['emissions_details']['summary'].get(c, {})
                        for p in r['stratum'][k][c]:
                            fb['emissions_details']['summary'][c][p] = fb['emissions_details']['summary'][c].get(p, {})
                            fb['emissions_details']['summary'][c][p][upper_k] = r['stratum'][k][c][p]

        # Note: We don't need to call
        #   datautils.multiply_nested_data(fb["emissions"], area)
        # because the consumption and heat data set in fc were assumed to
        # have been multiplied by area.

        # TODO: act on 'self.include_emissions_details'?  consume emissions
        #   doesn't provide as detailed emissions as FEPS and Prichard/O'Neill;
        #   it lists per-category emissions, not per-sub-category


##
## Helpers
##

def _calculate(calculator, fb, include_emissions_details):
    emissions_details = calculator.calculate(fb["consumption"])
    fb['emissions'] = copy.deepcopy(emissions_details['summary']['total'])
    if include_emissions_details:
        fb['emissions_details'] = emissions_details
