"""bluesky.sun

TODO: move this to pyairfire?
"""

import datetime

from math import acos, asin, cos, sin, tan
from math import degrees as deg, radians as rad

class Sun(object):
    """Calculates sunrise and sunset based on equations from NOAA:
    http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

    typical use, calculating the sunrise at the present day:

    from datetime import datetime
    s = Sun(lat=49,long=3)
    print s.sunrise(datetime.now())     # prints 'datetime.time(17, 58, 43)'
    print s.sunrise_hr(datetime.now())  # prints '18'

    Sun was copied from BlueSky Framework and significantly modified.
    TODO: acknoledge authors (STI?)
    """

    def __init__(self, lat=52.37, lng=4.90):  # default Amsterdam
        self.lat = lat
        self.lng = lng

    ##
    ## Public API
    ##

    def sunrise(self, day, utc_offset=0):
        """
        Return the time of sunrise as a datetime.time object.
        when is a datetime.datetime object. If none is given a
        local time zone is assumed (including daylight saving if present).
        """
        self._preptime(day)
        self._calc()
        return Sun._time_from_decimal_day(self.sunrise_t, utc_offset)

    def sunrise_hr(self, day, utc_offset=0):
        """
        Return the time of sunrise as an int.
        when is a datetime.datetime object. If none is given a
        local time zone is assumed (including daylight saving if present)
        """
        self._preptime(day)
        self._calc()
        return Sun._hour_from_decimal_day(self.sunrise_t, utc_offset)

    def sunset(self, day, utc_offset=0):
        self._preptime(day)
        self._calc()
        return Sun._time_from_decimal_day(self.sunset_t, utc_offset)

    def sunset_hr(self, day, utc_offset=0):
        self._preptime(day)
        self._calc()
        return Sun._hour_from_decimal_day(self.sunset_t, utc_offset)

    def solarnoon(self, day, utc_offset=0):
        self._preptime(day)
        self._calc()
        return Sun._time_from_decimal_day(self.solarnoon_t, utc_offset)

    ##
    ## 'Private' methods
    ##

    @staticmethod
    def _time_from_decimal_day(day, utc_offset):
        """
        returns a datetime.time object.
        day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """

        # TODO: return datetime object instead of time so that we know
        #   if hour is next day or previous day
        #   (e.g. if you want to know the GMT time of Seattle's sunset,
        #    or if you want to know the Seattle time of London's sunrise)

        hours = 24.0 * day + utc_offset
        h = int(hours)
        minutes = (hours - h) * 60
        m = int(minutes)
        seconds = (minutes - m) * 60
        s = int(seconds)
        return datetime.time(hour=h%24, minute=m, second=s)

    @staticmethod
    def _hour_from_decimal_day(day, utc_offset):
        """
        returns an int representing the hour of a given
        day as a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """

        # TODO: return datetime object instead of time so that we know
        #   if hour is next day or previous day
        #   (e.g. if you want to know the GMT time of Seattle's sunset,
        #    or if you want to know the Seattle time of London's sunrise)

        # TODO: refactor this to call _time_from_decimal_day, or vice-versa

        hours  = 24.0 * day + utc_offset
        h = int(hours)
        minutes= (hours - h) * 60
        m = int(minutes)
        return ((h + 1) if m > 29 else h) %24

    def _preptime(self, day):
        """
        Extract information in a suitable format from when,
        a datetime.datetime object.
        """
        # datetime days are numbered in the Gregorian calendar
        # while the calculations from NOAA are distibuted as
        # OpenOffice spreadsheets with days numbered from
        # 1/1/1900. The difference are those numbers taken for
        # 18/12/2010
        # daynumber 1=1/1/1900
        self.day = day.toordinal() - (734124 - 40529)
        # percentage past midnight, i.e. noon  is 0.5
        #self.time= 0.5 #(t.hour + t.minute / 60.0 + t.second / 3600.0) / 24.0

    def _calc(self):
        """
        Perform the actual calculations for sunrise, sunset and
        a number of related quantities.

        The results are stored in the instance variables
        sunrise_t, sunset_t and solarnoon_t
        """
        longitude = self.lng     # in decimal degrees, east is positive
        latitude = self.lat       # in decimal degrees, north is positive

        Jday = self.day + 2415018.5  # Julian day
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

        hourangle = deg(acos(cos(rad(90.833))/(cos(rad(latitude))*cos(rad(declination)))-tan(rad(latitude))*tan(rad(declination))))

        self.solarnoon_t = (720 - 4 * longitude - eqtime) / 1440
        self.sunrise_t = self.solarnoon_t - hourangle * 4 / 1440
        self.sunset_t = self.solarnoon_t + hourangle * 4 / 1440
