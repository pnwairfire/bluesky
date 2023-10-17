import datetime
import logging

from .hysplit_utils import DUMMY_PLUMERISE_HOUR
from .. import GRAMS_PER_TON, SQUARE_METERS_PER_ACRE


def get_emissions_rows_data(fire, dt, config, reduction_factor):

    (dummy, plumerise_hour, pm25_emitted, hourly_area) = _get_hour_data(dt, fire)

    area_meters, pm25_entrained, pm25_injected, heat = _get_emissions_params(
        pm25_emitted, plumerise_hour, hourly_area, dummy, config)
    heights, fractions = _reduce_and_reallocate_vertical_levels(
        plumerise_hour, reduction_factor)

    # if reduction factor == 20 (i.e. one height), add
    # pm25_entrained to pm25_injected
    if len(heights) == 1:
        pm25_injected += pm25_entrained
        pm25_entrained = 0

    # Inject the smoldering fraction of the emissions at ground level
    # (SMOLDER_HEIGHT represents a value slightly above ground level)
    height_meters = config("SMOLDER_HEIGHT")

    # Write the smoldering record to the file
    record_fmt = "%s %s %8.4f %9.4f %6.0f %7.2f %7.2f %15.2f\n"
    rows = [(height_meters, pm25_injected, area_meters, heat)]
    for height, fraction in zip(heights, fractions):
        height_meters = 0.0 if dummy else height
        pm25_injected = 0.0 if dummy else pm25_entrained * fraction

        rows.append((height_meters, pm25_injected, area_meters, heat))

    return rows, dummy

def _get_hour_data(dt, fire):
    if fire.plumerise and fire.timeprofiled_emissions and fire.timeprofiled_area:
        local_dt = dt + datetime.timedelta(hours=fire.utc_offset)
        # TODO: will fire.plumerise and fire.timeprofile always
        #    have string value keys
        local_dt = local_dt.strftime('%Y-%m-%dT%H:%M:%S')
        plumerise_hour = fire.plumerise.get(local_dt)
        timeprofiled_emissions_hour = fire.timeprofiled_emissions.get(local_dt)
        hourly_area = fire.timeprofiled_area.get(local_dt)
        if plumerise_hour and timeprofiled_emissions_hour and hourly_area:
            return (False, plumerise_hour,
                timeprofiled_emissions_hour.get('PM2.5', 0.0), hourly_area)

    # If we don't have real data for the given timestep, we apparently need
    # to stick in dummy records anyway (so we have the correct number of sources).
    logging.debug("Fire %s has no emissions for hour %s", fire.id,
        dt.strftime('%Y-%m-%dT%H:%M:%SZ'))

    return (True, DUMMY_PLUMERISE_HOUR, 0.0, 0.0)

def _get_emissions_params(pm25_emitted, plumerise_hour, hourly_area, dummy, config):
    if dummy:
        return 0.0, 0.0, 0.0, 0.0

    # convert area from acres to square meters.
    area_meters = hourly_area * SQUARE_METERS_PER_ACRE

    # Compute the total PM2.5 emitted at this timestep (grams) by
    # multiplying the phase-specific total emissions by the
    # phase-specific hourly fractions for this hour to get the
    # hourly emissions by phase for this hour, and then summing
    # the three values to get the total emissions for this hour
    pm25_emitted *= GRAMS_PER_TON

    # Total PM2.5 smoldering (not lofted in the plume)
    smoldering_fraction = plumerise_hour['smolder_fraction']
    if config("USE_CONST_SMOLDERING_FRACTION"):
        smoldering_fraction = config("SMOLDERING_FRACTION_CONST")
    pm25_injected = pm25_emitted * smoldering_fraction

    # Total PM2.5 lofted in the plume
    entrainment_fraction = 1.0 - smoldering_fraction
    pm25_entrained = pm25_emitted * entrainment_fraction

    # We don't assign any heat, so the PM2.5 mass isn't lofted
    # any higher.  This is because we are assigning explicit
    # heights from the plume rise.
    heat = 0.0

    return area_meters, pm25_entrained, pm25_injected, heat

def _reduce_and_reallocate_vertical_levels(plumerise_hour, reduction_factor):
    """The first step is to apply the reduction factor.

    After applying the reduction factor, we want zero emissions in the
    top level, whose emissions are allocated to the other levels based on
    their proportion of the remaining emissions.

    For example, if the reduction factor is 5 and the plume fractions are
    the following:

       [
          0.05, 0.05, 0.1, 0.1, 0.1,
          0.04, 0.04, 0.04, 0.04, 0.04,
          0.04, 0.04, 0.04, 0.04, 0.04,
          0.04, 0.04, 0.04, 0.04, 0.04
       ]

    That would get reduced to the following:

       [0.4, 0.2, 0.2, 0.2]

    And the last 0.2 would get allocated to the first three to get ths
    following:

       [0.5, 0.25, 0.25, 0.0]

    Note that, if the reduction factor is 20, then all emissions are
    included in the smoldering emissions, written above
    """
    heights = []
    fractions = []

    ## Reduce

    num_heights = len(plumerise_hour['heights']) - 1
    for level in range(0, num_heights, reduction_factor):
        lower_height = plumerise_hour['heights'][level]
        upper_height_index = min(level + reduction_factor, num_heights)
        upper_height = plumerise_hour['heights'][upper_height_index]
        if reduction_factor == 1:
            height_meters = (lower_height + upper_height) / 2.0  # original approach
        else:
            height_meters = upper_height # top-edge approach
        heights.append(height_meters)

        fractions.append(sum(plumerise_hour['emission_fractions'][level:level+reduction_factor]))

    ## Allocation top level's emissions to the rest
    num_heights = len(heights)
    if num_heights > 1:
        if fractions[-1] == 1:
            # all emissions in top level
            f = 1 / (num_heights-1)
            fractions = ([f] * (num_heights-1)) + [0]
        else:
            factor = 1 / (1 - fractions[-1])
            fractions = [f * factor for f in fractions[:-1]] + [0]

    return heights, fractions
