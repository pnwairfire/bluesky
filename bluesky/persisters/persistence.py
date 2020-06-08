#******************************************************************************
#
#  BlueSky Framework - Controls the estimation of emissions, incorporation of 
#                      meteorology, and the use of dispersion models to 
#                      forecast smoke impacts from fires.
#  Copyright (C) 2003-2006  USDA Forest Service - Pacific Northwest Wildland 
#                           Fire Sciences Laboratory
#  BlueSky Framework - Version 3.5.1    
#  Copyright (C) 2007-2009  USDA Forest Service - Pacific Northwest Wildland Fire 
#                      Sciences Laboratory and Sonoma Technology, Inc.
#                      All rights reserved.
#
# See LICENSE.TXT for the Software License Agreement governing the use of the
# BlueSky Framework - Version 3.5.1.
#
# Contributors to the BlueSky Framework are identified in ACKNOWLEDGEMENTS.TXT
#
#******************************************************************************

from datetime import timedelta
import logging
import copy

from bluesky.config import Config

class Persistence(object):
    _version_ = '2.0.0'
    # def __init__(self, fire_failure_handler):
    #     self.fire_failure_handler = fire_failure_handler

    def run(self, fires_manager):
        n_created = self._fill_missing_fires(fires_manager)

        logging.info('Persistence model created %d new fire records' % n_created)

    def _fill_missing_fires(self, fires_manager):
        """Fill-in (persist) that do not extend to the end of the emissions period"""
        n_created = 0
        first_hour, num_hours = self._get_time(fires_manager)
        last_hour = first_hour + timedelta(hours=num_hours)

        for fire in fires_manager.fires:
            with fires_manager.fire_failure_handler(fire):
                aa = fire["activity"]
                if len(aa) != 1:
                    raise ValueError("Each fire must have only 1 activity object when running persistence")
                if len(aa[0]["active_areas"]) != 1:
                    raise ValueError("Each fire must have only 1 active area when running persistence")
                start = aa[0]["active_areas"][0]["start"] + timedelta(days=1)
                end = aa[0]["active_areas"][0]["end"] + timedelta(days=1)

                while start <= last_hour:
                    n_created += 1
                    new_aa = copy.deepcopy(aa[0])
                    new_aa["active_areas"][0]["start"] = start
                    new_aa["active_areas"][0]["end"] = end
                    fire["activity"].append(new_aa)
                    start += timedelta(days=1)
                    end += timedelta(days=1)

        return n_created

    def _get_time(self, fires_manager):
        SECONDS_PER_HOUR = 3600
        start = Config().get('dispersion', 'start')
        num_hours = Config().get('dispersion', 'num_hours')

        if not start or num_hours is None:
            s = fires_manager.earliest_start # needed for 'start' and 'num_hours'
            if not s:
                raise ValueError("Unable to determine dispersion 'start'")
            if not start:
                start = s

            if not num_hours and start == s:
                e = fires_manager.latest_end # needed only for num_hours
                if e and e > s:
                    num_hours = int((e - s).total_seconds() / SECONDS_PER_HOUR)
            if not num_hours:
                raise ValueError("Unable to determine dispersion 'num_hours'")

        logging.debug("Dispersion window: %s for %s hours", start, num_hours)
        return start, num_hours
