__author__      = "Tobias Schmidt"

import os
import subprocess
import logging
import csv

from datetime import timedelta, time, datetime, timezone
from math import acos, asin, cos, sin, tan, exp, log, pow, sqrt, pi
from math import degrees as deg, radians as rad

from pyairfire import sun

# required executables
FEPS_WEATHER_BINARY = "feps_weather"
FEPS_TIMEPROFILE_BINARY = "feps_timeprofile"

class UbcBsfFEPSTimeProfiler(object):
    """ FEPS Time Profile Module

    FEPSTimeProfile was copied from BlueSky Framework, and subsequently modified
    TODO: acknowledge original authors (STI?)
    """

    # Setup the array that defines percentage of acres burned per hour for a
    # wildfire.  The array goes from midnight (hr 0) to 11 pm local time, in
    # decimal %, and total = 1.0.
    # Data from the Air Sciences Report to the WRAP. "Integrated Assessment Update
    # and 2018 Emissions Inventory for Prescribed Fire, Wildfire, and Agricultural
    # Burning."
    WRAP_TIME_PROFILE = [ 0.0057, 0.0057, 0.0057, 0.0057, 0.0057, 0.0057,
                        0.0057, 0.0057, 0.0057, 0.0057, 0.0200, 0.0400,
                        0.0700, 0.1000, 0.1300, 0.1600, 0.1700, 0.1200,
                        0.0700, 0.0400, 0.0057, 0.0057, 0.0057, 0.0057 ]

    def config(self, key):
        return self._config[key]

    def __init__(self, active_area, local_working_dir, config):
        self._config = config
        self._run(active_area, local_working_dir)

    def _run(self, active_area, working_dir):
        if active_area["consumption"] is None:
            raise ValueError("Missing consumption data for Canadian timeprofiling")
        if len(active_area["specified_points"]) != 1:
            raise ValueError("There should be exactly one specified_point per activity object before running Canadian timeprofiling")

        diurnalFile = self._get_diurnal_file(active_area, active_area["specified_points"][0],working_dir)

        consumptionFile = os.path.join(working_dir, "cons.txt")
        growthFile = os.path.join(working_dir, "growth.txt")
        profileFile = os.path.join(working_dir, "profile.txt")

        self.writeConsumption(active_area, consumptionFile)
        self.writeGrowth(active_area, growthFile)

        # What interpolation mode are we using?
        interpType = self.config("interpolation_type")
        if not interpType: interpType = 1
        normalize = self.config("normalize")
        if normalize:
            normSwitch = "-n"
        else:
            normSwitch = "-d"

        timeProfileArgs = [FEPS_TIMEPROFILE_BINARY,
                        "-c", consumptionFile,
                        "-w", diurnalFile,
                        "-g", growthFile,
                        "-i", str(interpType),
                        normSwitch,
                        "-o", profileFile]

        subprocess.check_output(timeProfileArgs)

        self.hourly_fractions = self.readProfile(active_area["start"], profileFile)
        self.start_hour = active_area["start"]
        self.ONE_HOUR = timedelta(hours=1)

    def writeConsumption(self, active_area, filename):
        cons = active_area["consumption"]["summary"]

        # compute total area and average moisture_duff over all specified points
        area = sum([l['area'] for l in active_area['specified_points']])
        mduff = sum([
            l['moisture_duff'] for l in active_area['specified_points']
        ]) / len(active_area['specified_points'])

        f = open(filename, 'w')
        f.write("cons_flm={}\n".format(cons["flaming"] / area))
        f.write("cons_sts={}\n".format(cons["smoldering"] / area))
        f.write("cons_lts={}\n".format(cons["residual"] / area))
        f.write("cons_duff={}\n".format(cons["duff"] / area))
        f.write("moist_duff={}\n".format(mduff))
        f.close()

    def writeGrowth(self, active_area, filename):
        f = open(filename, 'w')
        f.write("day, hour, size\n")
        cumul_size = 0
        # Write area measurements using WRAP curve
        # NOTE: We are assuming that all fires are of the type WF.
        # This is based off of the standard being said by CWFIS and smartfire.
        # See the orginal framework's version of this method to see how it used to be done.
        for h, size_fract in enumerate(self.WRAP_TIME_PROFILE):
            day = h // 24
            hour = h % 24
            size = active_area["specified_points"][0]["area"] * size_fract
            cumul_size += size
            f.write("%d, %d, %f\n" %(day, hour, cumul_size))
        f.close()

    def readProfile(self, start_hour, profileFile):
        time_profile = {}
        for k in ["area_fraction", "flaming", "residual", "smoldering"]:
             time_profile[k] = []
        i = 0
        for row in csv.DictReader(open(profileFile, 'r'), skipinitialspace=True):
            if i > 23:
                break
            time_profile["area_fraction"].append(float(row["area_fract"]))
            time_profile["flaming"].append(float(row["flame"]))
            time_profile["residual"].append(float(row["residual"]))
            time_profile["smoldering"].append(float(row["smolder"]))
            i = i + 1

        return time_profile

    # The next 2 methods were copied from AirFire with some modifications
    def _get_diurnal_file(self, active_area, fire_location_info, working_dir):
        self._fill_fire_location_info(active_area, fire_location_info)

        weather_file = os.path.join(working_dir, "weather.txt")
        diurnal_file = os.path.join(working_dir, "diurnal.txt")

        f = open(weather_file, 'w')
        f.write("sunsetTime=%d\n" % fire_location_info['sunset_hour'])  # Time of sun set
        f.write("middayTime=%d\n" % fire_location_info['max_temp_hour'])  # Time of max temp
        f.write("predawnTime=%d\n" % fire_location_info['min_temp_hour'])   # Time of min temp
        f.write("minHumid=%f\n" % fire_location_info['min_humid'])  # Min humid
        f.write("maxHumid=%f\n" % fire_location_info['max_humid'])  # Max humid
        f.write("minTemp=%f\n" % fire_location_info['min_temp'])  # Min temp
        f.write("maxTemp=%f\n" % fire_location_info['max_temp'])  # Max temp
        f.write("minWindAtFlame=%f\n" % fire_location_info['min_wind']) # Min wind at flame height
        f.write("maxWindAtFlame=%f\n" % fire_location_info['max_wind']) # Max wind at flame height
        f.write("minWindAloft=%f\n" % fire_location_info['min_wind_aloft']) # Min transport wind aloft
        f.write("maxWindAloft=%f\n" % fire_location_info['max_wind_aloft']) # Max transport wind aloft
        f.close()

        weather_args = [
            FEPS_WEATHER_BINARY,
            "-w", weather_file,
            "-o", diurnal_file
        ]
        # TODO: log output?
        subprocess.check_output(weather_args)

        return diurnal_file

    FIRE_LOCATION_INFO_DEFAULTS = {
        "min_wind": 6,
        "max_wind": 6,
        "min_wind_aloft": 6,
        "max_wind_aloft": 6,
        "min_humid": 40,
        "max_humid": 80,
        "min_temp": 13,
        "max_temp": 30,
        "min_temp_hour": 4,
        "max_temp_hour": 14,
        "snow_month": 5,
        "rain_days": 8,
        # In the old framework moisture_duff was set to 40. I decided to keep that
        # but note that in AirFire's BSP it is set to 100
        "moisture_duff": 40
    }
    def _fill_fire_location_info(self, fire_loc, fire_location_info):
        for k, v in list(self.FIRE_LOCATION_INFO_DEFAULTS.items()):
            if fire_location_info.get(k) is None:
                fire_location_info[k] = v
        if fire_location_info.get('sunset_hour') is None:
            dt = fire_loc['start']
            utc_offset = fire_loc['utc_offset']
            tmidday = datetime(dt.year, dt.month, dt.day, int(12))
            try:
                s = sun.Sun(lat=float(fire_loc["specified_points"][0]['lat']), lng=float(fire_loc["specified_points"][0]['lng']))
                fire_location_info['sunrise_hour'] = s.sunrise_hr(tmidday, int(utc_offset))
                fire_location_info['sunset_hour'] = s.sunset_hr(tmidday, int(utc_offset))
            except:
                # this calculation can fail near the North/South poles
                fire_location_info['sunrise_hour'] = 6
                fire_location_info['sunset_hour'] = 18
