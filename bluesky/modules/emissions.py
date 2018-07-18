"""bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import abc
import itertools
import logging
import sys

from emitcalc import __version__ as emitcalc_version
from emitcalc.calculator import EmissionsCalculator
from eflookup import __version__ as eflookup_version
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

import consume

from bluesky import datautils
from bluesky.exceptions import BlueSkyConfigurationError

from bluesky.consumeutils import (
    _apply_settings, FuelLoadingsManager, FuelConsumptionForEmissions, CONSUME_FIELDS
)

__all__ = [
    'run'
]
__version__ = "0.1.0"

TONS_PER_POUND = 0.0005 # 1.0 / 2000.0

INCLUDE_EMISSIONS_DETAILS_DEFAULT = False

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object

    Config options:
     - emissions > model -- emissions model to use
     - emissions > efs -- deprecated synonym for 'model'
     - emissions > species -- whitelist of species to compute emissions for
     - emissions > include_emissions_details -- whether or not to include
        emissions per fuel category per phase, as opposed to just per phase
     - emissions > fuel_loadings --
     - consumption > fuel_loadings -- considered if fuel loadings aren't
        specified in the emissions config
    """
    # Supporting 'efs' for backwards compatibility
    # TODO: deprecate and remove support for 'efs'
    model = (fires_manager.get_config_value('emissions', 'model')
        or fires_manager.get_config_value('emissions', 'efs')
        or 'feps').lower()

    include_emissions_details = fires_manager.get_config_value('emissions',
        'include_emissions_details', default=INCLUDE_EMISSIONS_DETAILS_DEFAULT)
    fires_manager.processed(__name__, __version__, model=model,
        emitcalc_version=emitcalc_version, eflookup_version=eflookup_version)

    try:
        klass = getattr(sys.modules[__name__], model.capitalize())
        e = klass(fires_manager.fire_failure_handler,
            fires_manager.get_config_value)
    except AttributeError:
        raise BlueSkyConfigurationError(
            "Invalid emissions model: '{}'".format(model))

    e.run(fires_manager.fires)

    # fix keys
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for g in fire.growth:
                for fb in g['fuelbeds']:
                    _fix_keys(fb['emissions'])
                    if include_emissions_details:
                        _fix_keys(fb['emissions_details'])

    # For each fire, aggregate emissions over all fuelbeds per growth
    # window as well as across all growth windows;
    # include only per-phase totals, not per category > sub-category > phase
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            # TODO: validate that each fuelbed has emissions data (here, or below) ?
            for g in fire.growth:
                g['emissions'] = datautils.summarize([g], 'emissions',
                    include_details=False)
            fire.emissions = datautils.summarize(fire.growth, 'emissions',
                include_details=False)

    # summarise over all growth objects
    all_growth = list(itertools.chain.from_iterable(
        [f.growth for f in fires_manager.fires]))
    summary = dict(emissions=datautils.summarize(all_growth, 'emissions'))
    if include_emissions_details:
        summary.update(emissions_details=datautils.summarize(
            all_growth, 'emissions_details'))
    fires_manager.summarize(**summary)

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

    def __init__(self, fire_failure_handler, config_getter):
        self.fire_failure_handler = fire_failure_handler
        self.include_emissions_details = config_getter(
            'emissions', 'include_emissions_details',
            default=INCLUDE_EMISSIONS_DETAILS_DEFAULT)
        self.config_getter = config_getter
        self.species = config_getter('emissions', 'species', default=[])

    @abc.abstractmethod
    def run(self, fires):
        pass


##
## FEPS
##

class Feps(EmissionsBase):

    def __init__(self, fire_failure_handler, config_getter):
        super(Feps, self).__init__(fire_failure_handler, config_getter)

        # The same lookup object is used for both Rx and WF
        self.calculator = EmissionsCalculator(FepsEFLookup(),
            species=self.species)

    def run(self, fires):
        logging.info("Running emissions module FEPS EFs")

        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    def _run_on_fire(self, fire):
        if 'growth' not in fire:
            raise ValueError(
                "Missing growth data required for computing emissions")
        for g in fire['growth']:
            if 'fuelbeds' not in g:
               raise ValueError(
                    "Missing fuelbed data required for computing emissions")
            for fb in g['fuelbeds']:
                if 'consumption' not in fb:
                    raise ValueError(
                        "Missing consumption data required for computing emissions")
                _calculate(self.calculator, fb, self.include_emissions_details)
                # TODO: Figure out if we should indeed convert from lbs to tons;
                #   if so, uncomment the following
                # Note: According to BSF, FEPS emissions are in lbs/ton consumed.  Since
                # consumption is in tons, and since we want emissions in tons, we need
                # to divide each value by 2000.0
                # datautils.multiply_nested_data(fb['emissions'], TONS_PER_POUND)
                # if self.include_emissions_details:
                #     datautils.multiply_nested_data(fb['emissions_details'], TONS_PER_POUND)

##
## Urbanski
##

class Urbanski(EmissionsBase):

    def __init__(self, fire_failure_handler, config_getter):
        super(Urbanski, self).__init__(fire_failure_handler, config_getter)

    def run(self, fires):
        logging.info("Running emissions module with Urbanski EFs")

        # Instantiate two lookup object, one Rx and one WF, to be reused
        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    def _run_on_fire(self, fire):
        if 'growth' not in fire:
            raise ValueError(
                "Missing growth data required for computing emissions")

        for g in fire['growth']:
            if 'fuelbeds' not in g:
                raise ValueError(
                    "Missing fuelbed data required for computing emissions")
            for fb in g['fuelbeds']:
                if 'consumption' not in fb:
                    raise ValueError(
                        "Missing consumption data required for computing emissions")
                fccs2ef = Fccs2Ef(fb["fccs_id"], is_rx=(fire.type=="rx"))
                calculator = EmissionsCalculator(fccs2ef, species=self.species)
                _calculate(calculator, fb, self.include_emissions_details)
                # Convert from lbs to tons
                # TODO: Update EFs to be tons/ton in a) eflookup package,
                #   b) just after instantiating look-up objects, above,
                #   or c) just before calling EmissionsCalculator, above
                datautils.multiply_nested_data(fb['emissions'], TONS_PER_POUND)
                if self.include_emissions_details:
                    datautils.multiply_nested_data(fb['emissions_details'], TONS_PER_POUND)

##
## CONSUME
##


class Consume(EmissionsBase):

    def __init__(self, fire_failure_handler, config_getter):
        super(Consume, self).__init__(fire_failure_handler, config_getter)

        self.species = species and [e.upper() for e in species]

        all_fuel_loadings = (config_getter('emissions','fuel_loadings')
            or config_getter('consumption','fuel_loadings'))
        self.fuel_loadings_manager = FuelLoadingsManager(
            all_fuel_loadings=all_fuel_loadings)


    def run(self, fires):
        logging.info("Running emissions module with CONSUME")

        # look for custom fuel loadings first in the emissions config and then
        # in the consumption config

        for fire in fires:
            with self.fire_failure_handler(fire):
                self._run_on_fire(fire)

    def _run_on_fire(fire):
        logging.debug("Consume emissions - fire {}".format(fire.id))

        if 'growth' not in fire:
            raise ValueError(
                "Missing growth data required for computing emissions")

        # TODO: set burn type to 'activity' if fire.fuel_type == 'piles' ?
        if fire.fuel_type == 'piles':
            raise ValueError("Consume can't be used for fuel type 'piles'")
        burn_type = fire.fuel_type

        for g in fire['growth']:
            if 'fuelbeds' not in g:
                raise ValueError(
                    "Missing fuelbed data required for computing emissions")


            for fb in g['fuelbeds']:
                self._run_on_fuelbed(fb, g['location'], burn_type)

    def _run_on_fuelbed(fb, location, burn_type):
        if 'consumption' not in fb:
            raise ValueError(
                "Missing consumption data required for computing emissions")
        if 'heat' not in fb:
            raise ValueError(
                "Missing heat data required for computing emissions")

        fuel_loadings_csv_filename = self.fuel_loadings_manager.generate_custom_csv(
             fb['fccs_id'])
        area = (fb['pct'] / 100.0) * location['area']
        fc = FuelConsumptionForEmissions(fb["consumption"], fb['heat'],
            area, burn_type, fb['fccs_id'], location,
            fccs_file=fuel_loadings_csv_filename)

        e_fuel_loadings = self.fuel_loadings_manager.get_fuel_loadings(
            fb['fccs_id'], fc.FCCS)
        fb['emissions_fuel_loadings'] = e_fuel_loadings
        e = consume.Emissions(fuel_consumption_object=fc)

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
            #  subcategory; to match what feps and urbanski calculators
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
        #   doesn't provide as detailed emissions as FEPS and Urbanski;
        #   it lists per-category emissions, not per-sub-category


##
## Helpers
##

def _calculate(calculator, fb, include_emissions_details):
    emissions_details = calculator.calculate(fb["consumption"])
    fb['emissions'] = emissions_details['summary']['total']
    if include_emissions_details:
        fb['emissions_details'] = emissions_details
