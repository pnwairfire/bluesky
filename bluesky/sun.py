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
        """Computes datetime of sunrise as a datetime.datetime object.

        args:
         - day -- date (datetime.date) of sunrise
         - utc_offset -- UTC offset of time to return; default 0 (UTC)

        e.g. The sun rose/set at 6:43am/6:00pm in Seattle on 2015 March 4th.
        Given that Seattle's UTC offset is -8 at that time of year, calling
        `s.sunrise(d, -8)` will return `datetime.datetime(2016,3,4,6,45,51)`.
        Calling `s.sunrise(d)`, on the other hand, will return
        `datetime.datetime(2016,3,4,14,45,51)`
        """
        self._calc(day, utc_offset)
        return self._sunrise

    def sunrise_hr(self, day, utc_offset=0):
        """Computes hour (int) of sunrise, rounded to the nearest hour

        args:
         - day -- date (datetime.date) of sunrise
         - utc_offset -- UTC offset of time to return; default 0 (UTC)
        """
        self._calc(day, utc_offset)
        return self._rounded_hour(self._sunrise)

    def sunset(self, day, utc_offset=0):
        """Computes datetime of sunset as a datetime.datetime object.

        args:
         - day -- date (datetime.date) of sunset
         - utc_offset -- UTC offset of time to return; default 0 (UTC)

        e.g. The sun rose/set at 6:43am/6:00pm in Seattle on 2015 March 4th.
        Given that Seattle's UTC offset is -8 at that time of year, calling
        `s.sunset(d, -8)` will return `datetime.datetime(2016,3,4,17,56,27)`.
        Calling `s.sunrise(d)`, on the other hand, will return
        `datetime.datetime(2016,3,5,2,56,27)`
        """
        self._calc(day, utc_offset)
        return self._sunset

    def sunset_hr(self, day, utc_offset=0):
        """Computes hour (int) of sunset, rounded to the nearest hour

        args:
         - day -- date (datetime.date) of sunset
         - utc_offset -- UTC offset of time to return; default 0 (UTC)
        """
        self._calc(day, utc_offset)
        return self._rounded_hour(self._sunset)

    def solarnoon(self, day, utc_offset=0):
        """Computes datetime of solor noon as a datetime.datetime object.

        args:
         - day -- date (datetime.date) of sunset
         - utc_offset -- UTC offset of time to return; default 0 (UTC)
        """
        self._calc(day, utc_offset)
        return self._solarnoon

    ##
    ## 'Private' methods
    ##

    def _calc(self, day_date, utc_offset):
        """Perform the actual calculations for sunrise, sunset and
        a number of related quantities.
        """
        day = day_date.toordinal() - (734124 - 40529)

        Jday = day + 2415018.5  # Julian day
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

        hourangle = deg(acos(cos(rad(90.833))/(cos(rad(self.lat))*cos(rad(declination)))-tan(rad(self.lat))*tan(rad(declination))))

        solarnoon_t = (720 - 4 * self.lng - eqtime) / 1440
        sunrise_t = solarnoon_t - hourangle * 4 / 1440
        sunset_t = solarnoon_t + hourangle * 4 / 1440

        self._sunrise = self._datetime_from_decimal_day(sunrise_t, day_date, utc_offset)
        self._sunset = self._datetime_from_decimal_day(sunset_t, day_date, utc_offset)
        self._solarnoon = self._datetime_from_decimal_day(solarnoon_t, day_date, utc_offset)

    def _datetime_from_decimal_day(self, day_decimal, day_date, utc_offset):
        """
        returns a datetime.time object.
        day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """

        # TODO: return datetime object instead of time so that we know
        #   if hour is next day or previous day
        #   (e.g. if you want to know the GMT time of Seattle's sunset,
        #    or if you want to know the Seattle time of London's sunrise)
        offset_days = 0
        hours = 24.0 * day_decimal + utc_offset
        if hours > 24.0:
            offset_days = int(hours / 24.0) # should be at most 1
            hours = hours % 24
        elif hours < 0.0:
            offset_days = -1 + int(hours / 24.0) # should be at most 1
            hours = hours + 24.0*abs(offset_days)

        h = int(hours)
        minutes = (hours - h) * 60
        m = int(minutes)
        seconds = (minutes - m) * 60
        s = int(seconds)

        # TODO: set datetime information in datetime.datetime object ?
        dt = datetime.datetime(year=day_date.year, month=day_date.month,
            day=day_date.day, hour=h, minute=m, second=s)
        return dt + datetime.timedelta(days=offset_days)

    def _rounded_hour(self, dt):
        """Returns datetime's hour, rounded to the nearest hour
        """
        return  (dt + datetime.timedelta(hours=int(dt.minute > 29))).hour
