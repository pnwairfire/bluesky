"""bluesky.met.arlprofiler

This module wraps the fortran arl profile utility.  Unless an absolute or
relative path to profile is provided on ArlProfile instantiation, profile
is expected to be in a directory in the search path. (This module prevents
configuring relative or absolute paths to hysplit, to eliminiate security
vulnerabilities when invoked by web service request.) To obtain profile,
contact NOAA.

TODO: move this to pyairfire or into it's own repo (arl-profile[r]) ?
"""

__author__      = "Joel Dubowy and others (unknown)"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import os
import subprocess
from datetime import date, datetime, time, timedelta
from math import acos, asin, cos, sin, tan, exp, log, pow
from math import degrees as deg, radians as rad

from bluesky.datetimeutils import parse_datetimes

__all__ = [
    'ArlProfiler'
]

ONE_HOUR = timedelta(hours=1)

class ArlProfiler(object):
    def __init__(self, met_files, profile_exe=None):
        """Constructor

        Carries out initialization and validation

        args:
         - met_files
        kwargs:
         - profile_exe

        met_files is expected to be a list of dicts, each dict specifying an
        arl met file along with a 'first', 'start', and 'end' datetimes. For
        example:
           [
              {"file": "...", "first_hour": "...", "last_hour": "..."}
           ]
        'first' is the first hour in the arl file. 'start' and 'end' define
        the time window for which local met data is desired.  Though fire
        growth windows don't have to start or end on the hour, 'first',
        'start', and 'end' do.

        'first', 'start', and 'end' are all assumed to be UTC.
        """
        # _parse_met_files validates information in met_files
        self._met_files = self._parse_met_files(met_files)

        # make sure profile_exe is a valid fully qualified pathname to the
        # profile exe or that it's
        profile_exe = profile_exe or 'profile'
        try:
            # Use check_output so that output isn't sent to stdout
            output = subprocess.check_output([profile_exe])
        except OSError:
            raise ValueError(
                "{} is not an existing/valid profile executable".format(profile_exe))
        self._profile_exe = profile_exe

    # TODO: is there a way to tell 'profile' to write profile.txt and MESSAGE
    #  to an alternate dir (e.g. to a /tmp/ dir)
    PROFILE_OUTPUT_FILE = './profile.txt'

    def profile(self, lat, lng, local_start, local_end, utc_offset, time_step=None):
        """Returns local met profile for specific location and timewindow

        args:
         - lat -- latitude of location
         - lng -- longitude of location
         - local_start -- local datetime object representing beginning of time window
         - local_end -- local datetime object representing end of time window
         - utc_offset -- hours ahead of or behind UTC

        kwargs:
         - time_step -- time step of arl file; defaults to 1
        """
        # TODO: validate utc_offset?
        if local_start > local_end:
            raise ValueError("Invalid localmet time window: start={}, end={}".format(
              local_start, local_end))

        utc_start = local_start - timedelta(hours=utc_offset)
        utc_start_hour = datetime(utc_start.year, utc_start.month,
            utc_start.day, utc_start.hour)
        utc_end = local_end - timedelta(hours=utc_offset)
        utc_end_hour = datetime(utc_end.year, utc_end.month, utc_end.day,
            utc_end.hour)
        # Don't include end hour if it's on the hour
        # TODO: should we indeed exclude it?
        if utc_end == utc_end_hour:
            utc_end_hour -= ONE_HOUR

        time_step = time_step or 1
        # TODO: make sure time_step is integer

        full_path_profile_txt = os.path.abspath(self.PROFILE_OUTPUT_FILE)
        local_met_data = {}
        for met_file in self._met_files:
            if (met_file['first_hour'] > utc_end_hour or
                    met_file['last_hour'] < utc_start_hour):
                # met file has no data within given timewindow
                continue

            start = max(met_file['first_hour'], utc_start_hour)
            end = min(met_file['last_hour'], utc_end_hour)

            d, f = os.path.split(met_file["file"])
            # split returns dir without trailing slash, which is required by profile
            d = d + '/'

            self._call(d, f, lat, lng, time_step)
            lmd = self._load(full_path_profile_txt, met_file['first_hour'],
                start, end, utc_offset, lat, lng)
            local_met_data.update(lmd)
        return local_met_data

    def _parse_met_files(self, met_files):
        logging.debug("Parsing met file specifications")
        if not met_files:
            raise ValueError(
                "ArlProfiler can't be instantiated without met files defined")

        # TODO: make sure ranges in met_files don't overlap

        # don't override values in original
        _met_files = []
        for met_file in met_files:
            # parse datetimes, and make sure they're valid
            _met_file = parse_datetimes(met_file, 'first_hour', 'last_hour')
            for k in 'first_hour', 'last_hour':
                d = _met_file[k]
                if datetime(d.year, d.month, d.day, d.hour) != d:
                    raise ValueError("ARL file's first_hour and last_hour times must be round hours")
            if _met_file['first_hour'] > _met_file['last_hour']:
                raise ValueError("ARL file's last hour can't be before ARL file's first first")

            # make sure file exists
            if not met_file.get("file"):
                raise ValueError("Arl met file not defined")
            _met_file["file"] = os.path.abspath(met_file.get("file"))
            if not os.path.isfile(_met_file["file"]):
                raise ValueError("{} is not an existing file".format(
                    _met_file["file"]))
            _met_files.append(_met_file)
        return _met_files


    def _call(self, d, f, lat, lng, time_step):
        # TODO: cd into tmp dir before calling, or somehow specify
        # custom tmp file name for profile.txt
        # TODO: add another method for calling profile?
        # Note: there must be no space between each option and it's value
        # Note: '-w2' indicates wind direction, instead of components
        cmd = "{exe} -d{dir} -f{file} -y{lat} -x{lng} -w2 -t{time_step}".format(
            exe=self._profile_exe, dir=d, file=f, lat=lat,
            lng=lng, time_step=time_step)
        logging.debug("Calling '{}'".format(cmd))
        # Note: if we need the stdout/stderr output, we can use:
        #  > output = subprocess.check_output(cmd.split(' '),
        #        stderr=subprocess.STDOUT)
        # or do something like:
        #  > output = StringIO.StringIO()
        #  > status = subprocess.check_output(cmd.split(' '),
        #        stdout=output, stderr=subprocess.STDOUT)
        # TODO: if writing to '/dev/null' isn't portable, capture stdout/stderr
        # in tmp file or in StringIO.StringIO object, and just throw away
        status = subprocess.call(cmd.split(' '),
            stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
        if status:
            raise RuntimeError("profile failed with exit code {}".format(
                status))

    def _load(self, full_path_profile_txt, first, start, end, utc_offset, lat, lng):
        logging.debug("Loading {}".format(full_path_profile_txt))
        # data = {}
        # with open(full_path_profile_txt, 'w') as f:
        #     for line in f....
        profile = ARLProfile(full_path_profile_txt, first, start, end,
            utc_offset, lat, lng)
        local_hourly_profile = profile.get_hourly_params()

        # TDOO: manipulate local_hourly_profile[dt] at all (e.g. map keys to
        # more human readable ones...look in SEVPlumeRise for mappings, and remove
        # code from there if mapping is done here) ?

        return {k.isoformat(): v for k,v in local_hourly_profile.items()}


class ARLProfile(object):
    """Reads raw ARL data from text file produced by 'profile', parses it
    into a complete dataset, fills in data, and converts to local time.

    To aid clarity, here is an example of one hour of the output
    file ('profile.txt') that we are parsing:

        ___________________________________________________
         Profile Time:  13  1  2  0  0
         Profile Location:    40.61 -100.56  ( 93, 65)

               TPP3  T02M  RH2M  U10M  V10M  PRSS
                                             hPa
         1013     0     0     0     0     0     0

               UWND  VWND  HGTS  TEMP  WWND  RELH     TPOT  WDIR  WSPD
                m/s   m/s          oC  mb/h     %       oK   deg   m/s
         1000   2.6  0.96   196 -0.50     0  66.0    272.7 247.6   2.8
          975   2.6   1.2   397  -1.8     0  66.0    273.4 243.6   2.8
          950   2.7   1.1   603  -3.1     0  66.0    274.1 244.6   2.9
          925   2.5  0.91   813  -5.0     0  67.0    274.2 247.6   2.7
          900   7.6  -1.9  1029  -3.1   6.2  40.0    278.3 282.0   7.8
          875   6.8  -3.5  1252  -2.9   6.2  50.0    280.8 294.8   7.6
          850   7.1  -3.2  1481  -4.5   6.0  60.0    281.4 291.8   7.7
          800   7.6  -3.1  1955  -7.7   2.6  63.0    283.0 289.7   8.2
          750   7.0  -3.8  2454 -11.1  0.58  59.0    284.5 295.8   8.0
          700   6.9  -3.6  2980 -13.5     0  54.0    287.5 295.2   7.8
          650   8.5  -3.1  3541 -16.3     0  42.0    290.6 287.4   9.1
          600  10.7  -1.3  4138 -19.7  0.94  35.0    293.4 274.6  10.8
          550   9.3  -1.3  4779 -23.3   1.6  29.0    296.5 275.9   9.4
          500   6.4  -2.3  5470 -28.2   1.2  22.0    298.6 287.4   6.8
          450   2.6  -4.0  6216 -33.7     0  22.0    300.9 324.3   4.8
          400  -1.6  -5.3  7032 -39.2  -3.3  26.0    304.1  14.5   5.6
          350  -2.4  -4.2  7933 -45.2 -0.85  26.0    307.8  27.7   4.9
          300   4.8  -1.1  8955 -47.5     0  19.0    318.4 281.0   5.0
          250  13.5   2.9 10154 -49.1  -1.1  11.0    333.1 255.5  13.8
          200  19.4   4.3 11618 -48.5   1.1   4.0    356.0 255.2  19.9
          150  28.1   6.9 13505 -51.9  0.52   9.0    380.7 253.8  29.0
          100  18.0   4.8 16116 -55.3 -0.75   2.0    421.0 252.7  18.7
           50   6.8 -0.15 20468 -60.8  0.54   2.0    500.2 268.9   6.8


    Unfortunately, the set of fields is not consistent.  Here's another
    example, from another profile.txt file:

        ___________________________________________________
         Profile Time:  14  5 30  0  0
         Profile Location:    37.43 -120.40  (136,160)

                PRSS  SHGT  T02M  U10M  V10M  PBLH  TPPA
                 hPa                                  mm
             0   996   112  31.5   2.6  -1.8     0     0

                PRES  UWND  VWND  WWND  TEMP  SPHU     TPOT  WDIR  WSPD
                       m/s   m/s  mb/h    oC  g/kg       oK   deg   m/s
           993   993   2.5  -1.9  -7.0  31.0   3.2    304.8 307.1   3.1
           984   984   2.5  -1.8  -7.0  29.5   3.0    304.0 305.4   3.1
           973   975   2.3  -1.7  -7.0  27.0   2.8    302.3 307.2   2.9
           958   961   2.4  -1.7  -7.0  25.5   2.5    302.1 305.5   3.0
           940   943   2.5  -1.7  -3.5  24.0   2.4    302.1 304.0   3.0
           918   922   2.6  -1.4  -5.3  22.1   2.4    302.2 299.0   2.9
           891   896   2.6 -0.80  -5.3  19.9   2.4    302.3 287.6   2.7
           855   862   2.3 -1E-1  -3.5  16.7   2.5    302.5 272.7   2.3
           811   820  0.75   1.5  -3.5  13.4   1.3    303.3 206.4   1.7
           766   778  -2.1   4.5  -3.5  11.8  0.24    306.2 155.5   5.0
           722   736  -2.3   3.8  -2.6   9.3  0.37    308.3 149.6   4.4
           662   678  -1.2   3.1  -1.8   4.8  0.33    310.6 158.9   3.4
           588   608   2.7   4.9  -1.3  -1.9  0.31    312.7 209.2   5.7
           520   544   6.5   7.8 -0.88  -8.7  0.85    314.8 219.8  10.2
           458   486   6.3  10.6 -0.66 -15.7  0.45    316.5 211.1  12.3
           402   432   8.8  13.1 -0.44 -22.1  0.75    319.3 214.0  15.8
           351   383  11.8  13.7 -0.33 -28.1  0.50    322.5 221.0  18.1
           304   339  16.4  14.5 -0.22 -34.3  0.46    325.6 228.9  21.9
           262   299  19.0  17.7 -0.11 -40.5  0.26    328.7 227.4  26.0
           224   263  17.5  20.1 -0.11 -47.7  0.11    330.5 221.4  26.6
           189   230  15.4  19.5 -1E-1 -54.5  5E-2    333.0 218.6  24.8
           158   200  16.2  18.3 -3E-2 -59.0  2E-2    339.1 221.9  24.4
           130   174  19.8  17.5 -2E-2 -57.7  2E-2    355.4 228.8  26.4
           106   150  19.6  15.6 -1E-2 -55.9  1E-2    373.6 231.8  25.1
            84   130  15.9  13.3 -1E-2 -57.1  1E-2    387.4 230.4  20.7
            65   112  11.6  10.6 -3E-3 -59.0  1E-2    400.4 228.0  15.7
            49  96.9   7.6   8.9 -2E-3 -60.7  1E-2    414.3 221.1  11.7
            35  83.6   3.8   9.1 -4E-4 -61.6  3E-3    430.2 202.8   9.8
            23  72.3  0.20   9.2 -2E-4 -62.0  1E-3    447.6 181.5   9.2
            13  62.4  -2.8   7.6 -3E-5 -61.9  1E-3    466.9 160.3   8.1
             4  53.9  -5.3   5.1     0 -61.3  2E-3    488.2 134.4   7.3


    ARLProfile was copied from BlueSky Framework, and subsequently modified
    TODO: acknoledge original authors (STI?)
    """

    def __init__(self, filename, first, start, end, utc_offset, lat, lng):
        self.raw_file = filename
        self.first = first
        self.start = start
        self.end = end
        self.utc_offset = utc_offset
        self.lat = lat
        self.lng = lng
        self.hourly_profile = {}

    def get_hourly_params(self):
        """ Read a raw profile.txt into an hourly dictionary of parameters """
        read_data = False
        hour_separator = "______"  # The output file uses this text string to separate hours.

        # read raw text into a dictionary
        profile = []
        hour_step = []
        with open(self.raw_file, 'r') as f:
            for line in f.readlines():
                if hour_separator in line:
                    read_data = True
                    profile.append(hour_step)
                    hour_step = []
                if read_data:
                    hour_step.append(line)
        if [] in profile: profile.remove([])

        if profile == []: return {}

        # process raw output into necessary data
        self.parse_hourly_text(profile)
        self.fix_first_hour()
        self.remove_below_ground_levels()
        self.spread_hourly_results()
        self.cast_strings_to_floats()
        self.fill_in_fields()
        self.utc_to_local()
        return self.hourly_profile

    def parse_hourly_text(self, profile):
        """ Parse raw hourly text into a more useful dictionary """
        for hour in profile:
            # 'date' is of the form: ['12', '6', '22', '18', '0']
            date = hour[1][hour[1].find(":") + 1:].strip().split()
            year = int(date[0]) if int(date[0]) > 1980 else (2000 + int(date[0]))
            t = datetime(year, int(date[1]), int(date[2]), int(date[3]))
            vars = {}

            # parameters appear on different line #s, for the two file types
            line_numbers = [4, 6, 8, 10] if hour[5][2:6].split() == [] else [4, 8, 10, 12]
            # parse at-surface variables
            first_vars = []
            first_vars.append('pressure_at_surface')
            for var_str in hour[line_numbers[0]].split():
                first_vars.append(var_str)
            first_vals = hour[line_numbers[1]].split()
            for v in xrange(len(first_vars)):
                vars[first_vars[v]] = []
                vars[first_vars[v]].append(first_vals[v])

            # parse variables at pressure levels
            main_vars = []
            main_vars.append("pressure")
            for var_str in hour[line_numbers[2]].split():
                main_vars.append(var_str)
            for v in main_vars:
                vars[v] = []
            for i in xrange(line_numbers[3], len(hour)):
                line = hour[i].split()
                if len(line) > 0:
                    for j in xrange(len(line)):
                        vars[main_vars[j]].append(line[j])

            self.hourly_profile[t] = vars

    def fix_first_hour(self):
        """
        Some ARL file keep a special place for at-surface met variables. However, sometimes these variables are not
        populated correctly at the zero hour (they will all be zero), and that needs to be fixed.
        """
        t = datetime(self.first.year, self.first.month, self.first.day)
        second_hr = t
        # find second hour in file
        for hr in xrange(1, 23):
            second_hr = datetime(int(t.year), int(t.month), int(t.day), int(hr))
            if second_hr in self.hourly_profile:
                break

        # back-fill first hour's values, if they are empty
        # These opaque variable names are defined by the ARL standard, and are described in types.ini
        if (float(self.hourly_profile[self.first]["PRSS"][0]) == 0.0
                and float(self.hourly_profile[self.first]["T02M"][0]) == 0.0):
            keys = [
                'pressure_at_surface', 'TPP3', 'T02M', 'RH2M', 'U10M', 'V10M', 'PRSS'
            ]
            self.hourly_profile[self.first].update(dict((k, self.hourly_profile[second_hr][k]) for k in keys))

    def remove_below_ground_levels(self):
        """
        Frequently, ARL files will include met variables at
        pressure levels that are below the surface of the Earth.
        This data is all nonsense, so it needs to be removed.
        """
        for dt, param_dict in self.hourly_profile.iteritems():
            surface_p = float(param_dict['pressure_at_surface'][0])
            if surface_p > float(param_dict['pressure'][0]) or surface_p < float(param_dict['pressure'][-1]):
                continue
            new_dict = {}
            for i in xrange(len(param_dict['pressure'])):
                if float(param_dict['pressure'][i]) < surface_p:
                    surface_index = i
                    break
            for k in param_dict.keys():
                # loop through each array, and append to new one
                if len(param_dict[k]) > 1:
                    new_array = []
                    for j in xrange(len(param_dict[k])):
                        if j >= surface_index:
                            new_array.append(float(param_dict[k][j]))
                    new_dict[k] = new_array
                elif len(param_dict[k]) == 1:
                    new_dict[k] = param_dict[k]

            # replace old dict with new
            del self.hourly_profile[dt]
            self.hourly_profile[dt] = new_dict

    def spread_hourly_results(self):
        """
        Frequently, ARL files will only have data every 3 or 6 hours.
        If so, we need to spread those values out to become hourly data.
        """
        # clean up unwanted hours of information
        for k in self.hourly_profile.keys():
            if k < self.start or k > (self.end):
                del self.hourly_profile[k]

        times = sorted(self.hourly_profile.keys())

        # spread values if the data is not hourly
        new_datetime = self.start
        while new_datetime <= self.end:
            if new_datetime not in times:
                closest_date = sorted(times, key=lambda d:abs(new_datetime - d))[0]
                self.hourly_profile[new_datetime] = self.hourly_profile[closest_date]
            new_datetime += ONE_HOUR

    def cast_strings_to_floats(self):
        # TODO: distinguish between floats and ints; use '<string>.isdigit()'
        # (which returns true if integer); can assume that, if string and not int,
        # then it's a float (?)
        for dt, hp in self.hourly_profile.items():
            for k in hp:
                if hasattr(hp[k], 'append'):
                    for i in range(len(hp[k])):
                        if hasattr(hp[k][i], 'strip'):
                            hp[k][i] = float(hp[k][i])
                elif hasattr(hp[k], 'strip'):
                    hp[k] = float(hp[k])

    def fill_in_fields(self):
        # The following is from BSF
        tmidday = datetime(self.first.year, self.first.month, self.first.day, 12)
        s = Sun(lat=self.lat, long=self.lng)
        sunrise = s.sunrise_hr(tmidday) + self.utc_offset
        sunset = s.sunset_hr(tmidday) + self.utc_offset
        # default Planetary Boundary Layer (PBL) step function
        default_pbl = lambda hr,sunrise,sunset: 1000.0 if (sunrise + 1) < hr < sunset else 100.0

        for dt, hp in self.hourly_profile.items():
            hr = (dt - self.first).total_seconds() / 3600.0
            hp['lat'] = self.lat
            hp['lng'] = self.lng
            for k in ['pressure', 'TPOT', 'WSPD', 'WDIR', 'WWND', 'TEMP', 'SPHU']:
                hp[k] = hp.get(k)
            if not hp.get('HGTS'):
                hp['HGTS'] = self.calc_height(hp['pressure'])
            if not hp.get('RELH'):
                hp['RELH'] = self.calc_rh(hp['pressure'], hp['SPHU'], hp['TEMP'])
            hp['dew_point'] = self.calc_dew_point(hp['RELH'], hp['TEMP'])
            hp['sunrise_hour'] = sunrise
            hp['sunset_hour'] = sunset
            for k in ['TO2M', 'RH2M', 'TPP3', 'TPP6', 'PBLH',
                    'T02M', 'U10M', 'V10M', 'PRSS', 'SHGT', 'TPPA',
                    'pressure_at_surface',]:
                self.list_to_scalar(hp, k, lambda: None)
            self.list_to_scalar(hp, 'HBPL',
                lambda: default_pbl(hr, sunrise, sunset))

    def list_to_scalar(self, hourly_profile, k, default):
        a = hourly_profile.get(k)
        if a is not None:
            if hasattr(a, 'append'):
                hourly_profile[k] = float(a[0])
            elif hasattr(a, 'strip'):
                hourly_profile[k] = float(a)
            # else, leave as is
        else:
            hourly_profile[k] = default()

    def calc_dew_point(self, rh, temp):
        """ dew_point_temp = (-5321/((ln(RH/100))-(5321/(273+T))))-273 """
        if not rh or not temp:
            return None

        dp = []
        for i in xrange(len(rh)):
            if float(rh[i]) < 1.0:
                dp.append((-5321.0 / ((-5.0) - (5321.0 / (273.0 + float(temp[i]))))) - 273.0)
            else:
                dp.append((-5321.0 / ((log(float(rh[i])/100.0)) - (5321.0 / (273.0 + float(temp[i]))))) - 273.0)

        return dp

    def calc_rh(self, pressure, sphu, temp):
        """
        SPHU=0.622*EVAP/PRES         ! specific humidity
        EVAP=RELH*ESAT               ! vapor pressure
        ESAT=EXP(21.4-(5351.0/TEMP)) ! saturation vapor pressure

        rh = EVAP / ESAT = (SPHU * PRES / 0.622) / (EXP(21.4-(5351.0/TEMP)))
        """
        if not pressure or not sphu or not temp:
            return None

        rh = map(lambda s,p,t: (float(s) * float(p) / 0.622) / (exp(21.4 - (5351.0 /(float(t) + 273.15)))), sphu,pressure,temp)
        # The above calculation is off by a factor of 10. Divide all values by 10
        return map(lambda h: h / 10.0, rh)

    P_SURFACE = 1000  # Psfc (mb)
    T_REF = 288.15    # Tref (K)
    LAPSE_RATE = 6.5  # Lapse Rate (K/km)
    G = 9.80665       # Gravitational Constant (m/s*s)
    Rd = 287.04       # Gas Constant

    def calc_height(self, pressure):
        """
        height =(Tref/(lapse_rate*0.001))*(1-(pressure/Psfc)^(gas_constant*lapse_rate*0.001/G))
        """
        if not pressure:
            return None

        return map(lambda p: (self.T_REF/(self.LAPSE_RATE*0.001))*(1.0 - pow(float(p)/self.P_SURFACE, self.Rd*self.LAPSE_RATE*0.001/self.G)), pressure)

    def utc_to_local(self):
        # profile dict will contain local met data index by *local* time
        local_hourly_profile = {}
        dt = self.start
        while dt <= self.end:
            logging.debug("Loading {}".format(dt.isoformat()))
            if dt not in self.hourly_profile:
                raise ValueError("{} not in arl file {}".format(dt.isoformat(),
                    full_path_profile_txt))

            local_hourly_profile[dt + timedelta(hours=self.utc_offset)] = self.hourly_profile[dt]
            dt += ONE_HOUR
        self.hourly_profile = local_hourly_profile

class Sun(object):
    """
    Calculate sunrise and sunset based on equations from NOAA:
    http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

    typical use, calculating the sunrise at the present day:

    from datetime import datetime
    s = Sun(lat=49,long=3)
    print s.sunrise(datetime.now())     # prints 'datetime.time(17, 58, 43)'
    print s.sunrise_hr(datetime.now())  # prints '18'

    Sun was copied from BlueSky Framework.
    TODO: acknoledge authors (STI?)
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
            self.timezone = offset.seconds / 3600.0

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

        hourangle = deg(acos(cos(rad(90.833))/(cos(rad(latitude))*cos(rad(declination)))-tan(rad(latitude))*tan(rad(declination))))

        self.solarnoon_t = (720 - 4 * longitude - eqtime + timezone * 60) / 1440
        self.sunrise_t = self.solarnoon_t - hourangle * 4 / 1440
        self.sunset_t = self.solarnoon_t + hourangle * 4 / 1440
