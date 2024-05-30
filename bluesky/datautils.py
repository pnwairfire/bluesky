"""bluesky.datautils

TODO: Remove this module and update all imports of this module to import
  from afdatetime.parsing directly
"""

__author__ = "Joel Dubowy"

import itertools

from pyairfire.data.utils import (
    deepmerge,
    summarize,
    multiply_nested_data,
    sum_nested_data,
    format_datetimes
)

def summarize_fuelbeds(obj, key, data_key_matcher=None):
    locations = obj.locations if hasattr(obj, 'locations') else [obj]
    locations = [loc for loc in locations if loc.get('fuelbeds')]
    obj[key] = summarize(locations, key, include_details=False,
        data_key_matcher=data_key_matcher)

def summarize_all_levels(fires_manager, key, data_key_matcher=None):
    """Aggregates data over all fuelbeds - per active_area,
    per activity collection, per fire, and across all fires

    Includes only per-phase totals, not per category > sub-category > phase
    """
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for ac in fire.get('activity', []):
                for aa in ac.active_areas:
                    for loc in aa.locations:
                        summarize_fuelbeds(loc, key, data_key_matcher=data_key_matcher)
                    summarize_fuelbeds(aa, key, data_key_matcher=data_key_matcher)
                summarize_fuelbeds(ac, key, data_key_matcher=data_key_matcher)
            summarize_fuelbeds(fire, key, data_key_matcher=data_key_matcher)

    summarize_over_all_fires(fires_manager, key, data_key_matcher=data_key_matcher)

def summarize_over_all_fires(fires_manager, key, data_key_matcher=None):
    # summarise over all activity objects
    all_locations = list(itertools.chain.from_iterable(
        [f.locations for f in fires_manager.fires]))
    all_locations = [loc for loc in all_locations if loc.get('fuelbeds')]
    summary = dict({key: summarize(all_locations, key, data_key_matcher=data_key_matcher)})
    fires_manager.summarize(**summary)
