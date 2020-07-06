__author__      = "Tobias Schmidt"

import os
import subprocess
import logging
import csv

from datetime import timedelta, time, datetime, timezone
from math import acos, asin, cos, sin, tan, exp, log, pow, sqrt, pi
from math import degrees as deg, radians as rad

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

    # NOTE FOR TOBIAS: FOR NOW fireLoc MEANS active_area
    def __init__(self, fireLoc, local_working_dir, config):
        self._config = config
        self._run(fireLoc, local_working_dir)

    # NOTE FOR TOBIAS: FOR NOW fireLoc MEANS active_area
    def _run(self, fireLoc, working_dir):

        if fireLoc["consumption"] is None:
            raise ValueError("Missing consumption data for Canadian timeprofiling")
        if len(fireLoc["specified_points"]) != 1:
            raise ValueError("There should be exactly one specified_point per activity object before running Canadian timeprofiling")

        diurnalFile = self._get_diurnal_file(fireLoc, fireLoc["specified_points"][0],working_dir)

        consumptionFile = os.path.join(working_dir, "cons.txt")
        growthFile = os.path.join(working_dir, "growth.txt")
        profileFile = os.path.join(working_dir, "profile.txt")

        self.writeConsumption(fireLoc, fireLoc["specified_points"][0], consumptionFile)
        self.writeGrowth(fireLoc, growthFile)

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

        self.hourly_fractions = self.readProfile(fireLoc["start"], profileFile)
        self.start_hour = fireLoc["start"]
        self.ONE_HOUR = timedelta(hours=1)

    def writeConsumption(self, fireLoc, fire_location_info, filename):
        f = open(filename, 'w')
        f.write("cons_flm=%f\n" % fireLoc["consumption"]["summary"]["flaming"])
        f.write("cons_sts=%f\n" % fireLoc["consumption"]["summary"]["smoldering"])
        f.write("cons_lts=%f\n" % fireLoc["consumption"]["summary"]["residual"])
        f.write("cons_duff=%f\n" % fireLoc["consumption"]["summary"]["duff"])
        f.write("moist_duff=%f\n" % fire_location_info["moisture_duff"])
        f.close()

    def writeGrowth(self, fireLoc, filename):
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
            size = fireLoc["specified_points"][0]["area"] * size_fract
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
    def _get_diurnal_file(self, fireLoc, fire_location_info, working_dir):
        self._fill_fire_location_info(fireLoc, fire_location_info)

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
        # "sunrise_hour": 6,
        # "sunset_hour": 18,
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
            time_zone = fire_loc['utc_offset']
            tmidday = datetime(dt.year, dt.month, dt.day, int(12), tzinfo = timezone(timedelta(seconds=time_zone*3600)))
            try:
                s = Sun(lat=float(fire_loc["specified_points"][0]['lat']), long=float(fire_loc["specified_points"][0]['lng']))
                fire_location_info['sunrise_hour'] = s.sunrise_hr(tmidday)
                fire_location_info['sunset_hour'] = s.sunset_hr(tmidday)
            except:
                # this calculation can fail near the North/South poles
                fire_location_info['sunrise_hour'] = 6
                fire_location_info['sunset_hour'] = 18
                

# This was copied from the old framework. It was originally created by STI.
# It has only minor changes to incorporate a different utc_offset datetime format.
# The original docs are below within the class.
class Sun(object):
    """
    Calculate sunrise and sunset based on equations from NOAA:
    http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

    typical use, calculating the sunrise at the present day:

    from datetime import datetime
    s = Sun(lat=49,long=3)
    print s.sunrise(datetime.now())     # prints 'datetime.time(17, 58, 43)'
    print s.sunrise_hr(datetime.now())  # prints '18'
    """
    def __init__(self, lat=52.37, long=4.90):  # default Amsterdam
        self.lat = lat
        self.long = long

    def sunrise(self, when):
        """
        Return the time of sunrise as a datetime.time object.
        when is a datetime.datetime object. If none is given a
        local time zone is assumed (including daylight saving if present).
        """
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimalday(self.sunrise_t)

    def sunrise_hr(self, when):
        """
        Return the time of sunrise as an int.
        when is a datetime.datetime object. If none is given a
        local time zone is assumed (including daylight saving if present)
        """
        self.__preptime(when)
        self.__calc()
        return Sun.__hourfromdecimalday(self.sunrise_t)

    def sunset(self, when):
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimalday(self.sunset_t)

    def sunset_hr(self, when):
        self.__preptime(when)
        self.__calc()
        return Sun.__hourfromdecimalday(self.sunset_t)

    def solar_radiation_hr(self, when):
        self.__preptime(when)
        self.__calc()
        return self.solar_radiation

    def solarnoon(self, when):
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimalday(self.solarnoon_t)

    @staticmethod
    def __timefromdecimalday(day):
        """
        returns a datetime.time object.
        day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """
        hours = 24.0 * day
        h = int(hours)
        minutes = (hours - h) * 60
        m = int(minutes)
        seconds = (minutes - m) * 60
        s = int(seconds)
        return time(hour=h, minute=m, second=s)

    @staticmethod
    def __hourfromdecimalday(day):
        """
        returns an int representing the hour of a given
        day as a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """
        hours  = 24.0 * day
        h = int(hours)
        minutes= (hours - h) * 60
        m = int(minutes)
        return (h + 1) if m > 29 else h

    def __preptime(self,when):
        """
        Extract information in a suitable format from when,
        a datetime.datetime object.
        """
        # datetime days are numbered in the Gregorian calendar
        # while the calculations from NOAA are distibuted as
        # OpenOffice spreadsheets with days numbered from
        # 1/1/1900. The difference are those numbers taken for
        # 18/12/2010
        self.day = when.toordinal() - (734124 - 40529)
        t = when.time()
        self.time= (t.hour + t.minute / 60.0 + t.second / 3600.0) / 24.0

        self.timezone = 0
        offset = when.utcoffset()
        if not offset is None:
            self.timezone = offset.total_seconds() / 3600.0

    def __calc(self):
        """
        Perform the actual calculations for sunrise, sunset and
        a number of related quantities.

        The results are stored in the instance variables
        sunrise_t, sunset_t and solarnoon_t
        """
        timezone = self.timezone  # in hours, east is positive
        longitude = self.long     # in decimal degrees, east is positive
        latitude = self.lat       # in decimal degrees, north is positive

        time = self.time          # percentage past midnight, i.e. noon  is 0.5
        day = self.day            # daynumber 1=1/1/1900

        Jday = day + 2415018.5 + time - timezone / 24  # Julian day
        Jcent = (Jday - 2451545) / 36525               # Julian century

        Manom = 357.52911 + Jcent * (35999.05029 - 0.0001537 * Jcent)
        Mlong = 280.46646 + Jcent * (36000.76983 + Jcent * 0.0003032) % 360
        Eccent = 0.016708634 - Jcent * (0.000042037 + 0.0001537 * Jcent)
        Mobliq = 23 + (26 + ((21.448 - Jcent * (46.815 + Jcent * (0.00059 - Jcent * 0.001813)))) / 60) / 60
        obliq = Mobliq + 0.00256 * cos(rad(125.04 - 1934.136 * Jcent))
        vary = tan(rad(obliq / 2)) * tan(rad(obliq / 2))
        Seqcent = sin(rad(Manom))*(1.914602-Jcent*(0.004817+0.000014*Jcent))+sin(rad(2*Manom))*(0.019993-0.000101*Jcent)+sin(rad(3*Manom))*0.000289
        Struelong = Mlong + Seqcent
        Sapplong = Struelong - 0.00569 - 0.00478 * sin(rad(125.04 - 1934.136 * Jcent))
        declination = deg(asin(sin(rad(obliq)) * sin(rad(Sapplong))))

        eqtime = 4*deg(vary*sin(2*rad(Mlong))-2*Eccent*sin(rad(Manom))+4*Eccent*vary*sin(rad(Manom))*cos(2*rad(Mlong))-0.5*vary*vary*sin(4*rad(Mlong))-1.25*Eccent*Eccent*sin(2*rad(Manom)))

        # http://www.jgiesen.de/astro/suncalc/calculations.htm
        zenith = 90.833 # approx. correction for atmospheric refraction at sunrise and sunset
        val = cos(rad(zenith))/(cos(rad(latitude))*cos(rad(declination)))-tan(rad(latitude))*tan(rad(declination))
        val = min(1, max(-1, val)) # clip the intermediate value so that it is not greater than 1 or less that -1
        hourangle = deg(acos(val))

        self.solarnoon_t = (720 - 4 * longitude - eqtime + timezone * 60) / 1440
        self.sunrise_t = self.solarnoon_t - hourangle * 4 / 1440
        self.sunset_t = self.solarnoon_t + hourangle * 4 / 1440

        
        # --- Calculate solar radiation ---

        # Get hour angle from time
        time_offset = eqtime - (4 * longitude) + (60 * timezone)
        tst = ((time * 1440) + time_offset) % 1440
        hourly_hourangle = (tst / 4) - 180

        # The altitude of the sun, the angle between horizon and centre of the sun's disc
        elevation_angle = asin(sin(rad(declination)) * sin(rad(latitude))
                            + cos(rad(declination)) * cos(rad(latitude)) * cos(rad(hourly_hourangle)))

        # Sine of solar elevation angle
        sinalp = sin(elevation_angle)

        try:
            # Optical air mass
            optam = 1.0 / (sinalp + 0.15 * ((asin(sinalp) * (180.0 / pi) + 3.885) ** (-1.253)))

            # Atmospheric transmission coefficient
            atmtc = 0.7

            # Assuming zero elevation
            elev = 0

            # Clear sky solar attenuation
            csa = atmtc ** (optam * (((288 - 0.0065 * elev) / 288) ** 5.256))

            # Solar constant - maximum amount of radiation W/m**2
            solar_constant = 1367

            # Solar radiation
            radiation = solar_constant * csa * sinalp
            if radiation > 0:
                self.solar_radiation = radiation
            else:
                self.solar_radiation = 0

        except ValueError:
            self.solar_radiation = 0