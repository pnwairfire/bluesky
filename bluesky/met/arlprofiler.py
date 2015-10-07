"""bluesky.arlprofiler

This module wraps the fortran arl profile utility.  Unless an absolute or
relative path to profile is provided on ArlProfile instantiation, profile
is expected to be in a directory in the search path. (This module prevents
configuring relative or absolute paths to hysplit, to eliminiate security
vulnerabilities when invoked by web service request.) To obtain profile,
contact NOAA.

TODO: move this to pyairfire or into it's own repo (arl-profile[r]) ?
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import os
import subprocess
from datetime import date, datetime, time, timedelta

from bluesky.datautils import parse_datetimes

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
              {"file": "...", "first": "...", "start": "...", "end": "..."}
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

    def profile(self, lat, lng, utc_offset, time_step=None):
        # TODO: validate utc_offset?

        time_step = time_step or 1
        # TODO: make sure time_step is integer

        full_path_profile_txt = os.path.abspath(self.PROFILE_OUTPUT_FILE)
        local_met_data = {}
        for met_file in self._met_files:
            d, f = os.path.split(met_file["file"])
            # split returns dir without trailing slash, which is required by profile
            d = d + '/'

            self._call(d, f, lat, lng, time_step)
            lmd = self._load(full_path_profile_txt, met_file['first'],
                met_file['start'], met_file['end'], utc_offset)
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
            _met_file = parse_datetimes(met_file, 'first', 'start', 'end')
            for k in 'first', 'start', 'end':
                d = _met_file[k]
                if datetime(d.year, d.month, d.day, d.hour) != d:
                    raise ValueError("Arl profile first, start, and end times must be round hours")
            if _met_file['first'] > _met_file['start']:
                raise ValueError("Start time can't be before ARL file's first time")
            if _met_file['start'] > _met_file['end']:
                raise ValueError("Start time can't be after end time")

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
        #  > output = subprocess.check_output(cmd_args,
        #        stderr=subprocess.STDOUT)
        # TODO: capture stdout/stderr
        status = subprocess.call(cmd.split(' '))
        if status:
            raise RuntimeError("profile failed with exit code {}".format(
                status))

    def _load(self, full_path_profile_txt, first, start, end, utc_offset):
        logging.debug("Loading {}".format(full_path_profile_txt))
        # data = {}
        # with open(full_path_profile_txt, 'w') as f:
        #     for line in f....
        profile = ARLProfile(full_path_profile_txt, first, start, end)
        hourly_profiles = profile.get_hourly_params()
        # profile dict will contain local met data index by *local* time
        profile_dict = {}
        dt = start
        while dt <= end:
            logging.debug("Loading {}".format(dt.isoformat()))
            if dt not in hourly_profiles:
                raise ValueError("{} not in arl file {}".format(dt.isoformat,
                    full_path_profile_txt))
            # TDOO: manipulate hourly_profiles[dt] at all?
            profile_dict[dt - timedelta(hours=utc_offset)] = hourly_profiles[dt]
            dt += ONE_HOUR
        return {k.isoformat(): v for k,v in profile_dict.items()}

class ARLProfile(object):
    """Reads raw ARL data in text file, parsing it into a complete dataset

    ARLProfile was copied from BlueSky Framework.
    TODO: acknoledge authors (STI?)
    """

    def __init__(self, filename, first, start, end):
        self.raw_file = filename
        self.first = first
        self.start = start
        self.end = end
        self.hourly_profile = {}

    ###############################################################
    # To aid clarity, here is an example of one hour of the output
    # files that we are parsing using the following method:
    #___________________________________________________
    # Profile Time:  13  1  2  0  0
    # Profile Location:    40.61 -100.56  ( 93, 65)
    #
    #       TPP3  T02M  RH2M  U10M  V10M  PRSS
    #                                     hPa
    # 1013     0     0     0     0     0     0
    #
    #       UWND  VWND  HGTS  TEMP  WWND  RELH     TPOT  WDIR  WSPD
    #        m/s   m/s          oC  mb/h     %       oK   deg   m/s
    # 1000   2.6  0.96   196 -0.50     0  66.0    272.7 247.6   2.8
    #  975   2.6   1.2   397  -1.8     0  66.0    273.4 243.6   2.8
    #  950   2.7   1.1   603  -3.1     0  66.0    274.1 244.6   2.9
    #  925   2.5  0.91   813  -5.0     0  67.0    274.2 247.6   2.7
    #  900   7.6  -1.9  1029  -3.1   6.2  40.0    278.3 282.0   7.8
    #  875   6.8  -3.5  1252  -2.9   6.2  50.0    280.8 294.8   7.6
    #  850   7.1  -3.2  1481  -4.5   6.0  60.0    281.4 291.8   7.7
    #  800   7.6  -3.1  1955  -7.7   2.6  63.0    283.0 289.7   8.2
    #  750   7.0  -3.8  2454 -11.1  0.58  59.0    284.5 295.8   8.0
    #  700   6.9  -3.6  2980 -13.5     0  54.0    287.5 295.2   7.8
    #  650   8.5  -3.1  3541 -16.3     0  42.0    290.6 287.4   9.1
    #  600  10.7  -1.3  4138 -19.7  0.94  35.0    293.4 274.6  10.8
    #  550   9.3  -1.3  4779 -23.3   1.6  29.0    296.5 275.9   9.4
    #  500   6.4  -2.3  5470 -28.2   1.2  22.0    298.6 287.4   6.8
    #  450   2.6  -4.0  6216 -33.7     0  22.0    300.9 324.3   4.8
    #  400  -1.6  -5.3  7032 -39.2  -3.3  26.0    304.1  14.5   5.6
    #  350  -2.4  -4.2  7933 -45.2 -0.85  26.0    307.8  27.7   4.9
    #  300   4.8  -1.1  8955 -47.5     0  19.0    318.4 281.0   5.0
    #  250  13.5   2.9 10154 -49.1  -1.1  11.0    333.1 255.5  13.8
    #  200  19.4   4.3 11618 -48.5   1.1   4.0    356.0 255.2  19.9
    #  150  28.1   6.9 13505 -51.9  0.52   9.0    380.7 253.8  29.0
    #  100  18.0   4.8 16116 -55.3 -0.75   2.0    421.0 252.7  18.7
    #   50   6.8 -0.15 20468 -60.8  0.54   2.0    500.2 268.9   6.8
    #
    #___________________________________________________
    ###############################################################
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


# 'profile' is assumed to be in search path, unless configured to point to
# another location (is that dangerous for web service?...maybe API
# requests shouldn't allow alternate 'profile' executable)

# profiler from BSF:
# https://bitbucket.org/fera/airfire-bluesky-framework/src/09f2c16d08128ba9bf5fdeb9a6c35c5a0632b2f2/src/base/fileIO/metData/arl_profiler/?at=master&fileviewer=file-view-default

# TODO: reuse any of the code from BSF's local_met_inforation module
# (copied below) ?



## BSF's local_met_information module:

# import os
# import re
# import fileinput
# from kernel.core import Process
# from kernel.types import construct_type
# from kernel.structure import Structure, TemporalStructure
# from kernel.bs_datetime import BSDateTime, utc, timezone_from_str, FixedOffset
# from kernel.config import config, baseDir
# from kernel import location
# from math import acos, asin, cos, sin, tan, exp, log, pow
# from math import degrees as deg, radians as rad
# from datetime import date, datetime, time, timedelta


# class LocalMetData(TemporalStructure):
#     """ Local Met information at a single, atomic fire location """

#     def __init__(self, otherdata=None):
#         if hasattr(otherdata, 'iteritems') or hasattr(otherdata, 'keys'):
#             TemporalStructure.__init__(self, otherdata)
#         else:
#             TemporalStructure.__init__(self)
#             if otherdata is not None:
#                 self["id"] = otherdata
#             else:
#                 self["id"] = "UNKNOWN"
#             # Clean up ID field.  Removes non-word chars and changes to all caps
#         self["id"] = re.sub(r"\W+", "", str(self["id"])).upper()
#         self.setdefault("metadata", dict())

#     def __repr__(self):
#         return "<%s>" % self.__str__()

#     def __str__(self):
#         return "LocalMetData: %s" % self["id"]

#     def uniqueid(self):
#         if self["date_time"] is None:
#             return self["id"]
#         run_day = (self["date_time"] - config.get("DEFAULT", "DATE", asType=BSDateTime)).days
#         return "%s.%s" % (self['id'], run_day)

#     def clone(self):
#         clone = type(self)(self["id"])
#         for k, v in self.iteritems():
#             if isinstance(v, Structure):
#                 value = v.clone()
#             elif isinstance(v, dict):
#                 value = dict(v)
#             elif isinstance(v, list):
#                 value = v[:]
#             else:
#                 value = v
#             clone[k] = value
#         return clone


# class LocalMetInformation(Structure):
#     """ Structure that contains information about available local meteorological data """

#     def __init__(self, otherdata=None):
#         Structure.__init__(self, otherdata)
#         self.setdefault("met_locations", list())
#         self.setdefault("metadata", dict())

#     def set_value(self, k, v, **kwargs):
#         if k not in self:
#             return False
#         if self.type_of(k).isArray:
#             if isinstance(v, list):
#                 v = [self.type_of(k).itemType.convertValue(vv) for vv in v]
#                 self[k] = v
#             else:
#                 if "hour" in kwargs:
#                     v = self.type_of(k).itemType.convertValue(v)
#                     self[k][kwargs['hour']] = v
#                 else:
#                     raise ValueError("Unable to assign scalar value to %s array" % k)
#         else:
#             self[k] = v
#         return True

#     def addLocation(self, locationData):
#         assert isinstance(locationData, LocalMetData)
#         self["met_locations"].append(locationData)

#     def locations(self):
#         """ IMPORTANT: Returns a COPY of the list of locations
#         This is a safeguard against calling removeLocation() while looping over this list.
#         """
#         return self["met_locations"][:]


# class ARLToLocalMet(Process):
#     """ Real local meteorological data from ARL met files."""

#     def init(self):
#         self.declare_input("met_info", "MetInfo")
#         self.declare_input("fires", "FireInformation")
#         self.declare_output("local_met", "LocalMetInformation")

#     def run(self, context):
#         met_info = self.get_input("met_info")
#         fireInfo = self.get_input("fires")
#         self.log.info("Reading met and fire data to produce local met info")

#         num_fires = 0
#         local_met_info = construct_type("LocalMetInformation")

#         for fireLoc in fireInfo.locations():
#             keys = ['id', 'latitude', 'longitude', 'date_time']
#             fire_data = dict((k, fireLoc[k]) for k in keys)
#             fire_data['unique_id'] = fireLoc.uniqueid()
#             met_file_list = self.find_correct_met_files(met_info, fire_data['date_time'])
#             local_met_info = self.read_arl_data(context, fire_data, local_met_info, met_file_list)
#             num_fires += 1

#         self.log.info("Successfully produced met data for %d fires", num_fires)
#         self.set_output("local_met", local_met_info)

#     def find_correct_met_files(self, met_info, dt):
#         """ Search through all the input met files and find those with the correct dates. """
#         met_file_list = []
#         start = dt.replace(hour=0)
#         end = dt.replace(hour=23)

#         # TODO: The logic below does not take into account nested met grids.
#         for f in met_info["files"]:
#             file_start = f.start
#             file_end = f.end
#             if start >= file_start and start <= file_end or end >= file_start and end <= file_end:
#                 met_file_list.append(f.filename)

#         if len(met_file_list) == 0:
#             string_date = str(dt.year) + "-" + str(dt.month) + "-" + str(dt.day)
#             self.log.info("A met file was not found for a fire on this date: " + string_date)

#         return met_file_list

#     def read_arl_data(self, context, fire_data, met_info, met_file_list):
#         """ Runs the Hysplit standard ARL profile executable to read the data from an ARL file. """
#         arl_profiler = os.path.join(baseDir, "base", "profile")
#         time_step = config.get("DEFAULT", "HOURS_PER_TIMESTEP", asType=int)
#         dt = fire_data['date_time']

#         # loop over each relavent met file
#         hourly_profile = {}
#         for met_filepath in met_file_list:
#             met_dir,met_file = os.path.split(met_filepath)

#             context.execute(arl_profiler,
#                             "-d" + met_dir + "/",
#                             "-f" + met_file,
#                             "-y" + str(fire_data['latitude']),   # latitude
#                             "-x" + str(fire_data['longitude']),  # longitude
#                             "-w2",                               # wind direction, instead of components
#                             "-t" + str(time_step)                # Is the met file 1, 3, or 6-hour data?
#             )

#             context.trash_file("MESSAGE")
#             output_filename = context.full_path("profile.txt")
#             profile = ARLProfile(output_filename, dt)
#             hourly_profile.update(profile.get_hourly_params())

#         return ARLToLocalMet.build_met_data(fire_data, hourly_profile, met_info)

#     @staticmethod
#     def build_met_data(fire_data, hourly_profile, met_info):
#         """ Build a LocalMetData object for each hour in a fire day """
#         # set time variables
#         dt = fire_data['date_time']
#         tz_str = str(dt.tzinfo.tzname(dt)).strip()
#         tz = ARLProfile.calc_tz(tz_str)
#         tmidday = datetime(dt.year, dt.month, dt.day, int(12))
#         # set sunrise/sunset variables
#         s = Sun(lat=float(fire_data['latitude']), long=float(fire_data['longitude']))
#         sunrise = s.sunrise_hr(tmidday) + tz
#         sunset = s.sunset_hr(tmidday) + tz
#         # default Planetary Boundary Layer (PBL) step function
#         default_pbl = lambda hr,sunrise,sunset: 1000.0 if (sunrise + 1) < hr < sunset else 100.0

#         for hr in xrange(len(hourly_profile)):
#             met_data = construct_type("LocalMetData")
#             met_data['id'] = fire_data['id']
#             met_data['latitude'] = fire_data['latitude']
#             met_data['longitude'] = fire_data['longitude']
#             met_data['date_time'] = BSDateTime(dt.year, dt.month, dt.day, hr)
#             this_hour = hourly_profile[datetime(dt.year, dt.month, dt.day, hr) - timedelta(hours=tz)]
#             met_data['pressure'] = this_hour.get('pressure', None)
#             # These opaque variable names are defined by the ARL standard, and are described in types.ini
#             met_data['HGTS'] = this_hour.get('HGTS', ARLToLocalMet.calc_height(met_data['pressure']))
#             met_data['TPOT'] = this_hour.get('TPOT', None)
#             met_data['WSPD'] = this_hour.get('WSPD', None)
#             met_data['WDIR'] = this_hour.get('WDIR', None)
#             met_data['WWND'] = this_hour.get('WWND', None)
#             met_data['TEMP'] = this_hour.get('TEMP', None)
#             met_data['SPHU'] = this_hour.get('SPHU', None)
#             met_data['RELH'] = this_hour.get('RELH', ARLToLocalMet.calc_rh(met_data['pressure'],
#                                                                            met_data['SPHU'],
#                                                                            met_data['TEMP']))
#             met_data['dew_point'] = ARLToLocalMet.calc_dew_point(met_data['RELH'], met_data['TEMP'])
#             met_data['TO2M'] = float(this_hour['TO2M'][0]) if 'TO2M' in this_hour else None
#             met_data['RH2M'] = float(this_hour['RH2M'][0]) if 'RH2M' in this_hour else None
#             met_data['TPP3'] = float(this_hour['TPP3'][0]) if 'TPP3' in this_hour else None
#             met_data['TPP6'] = float(this_hour['TPP6'][0]) if 'TPP6' in this_hour else None
#             met_data['PBLH'] = float(this_hour['PBLH'][0]) if 'PBLH' in this_hour else None
#             met_data['HPBL'] = float(this_hour['HPBL'][0]) if 'HPBL' in this_hour else default_pbl(hr, sunrise, sunset)

#             # set sunrise and sunset times
#             met_data['sunrise_hour'] = sunrise
#             met_data['sunset_hour'] = sunset

#             met_info.addLocation(met_data)

#         return met_info

#     @staticmethod
#     def calc_dew_point(rh, temp):
#         """ dew_point_temp = (-5321/((ln(RH/100))-(5321/(273+T))))-273 """
#         if not rh or not temp:
#             return None

#         dp = []
#         for i in xrange(len(rh)):
#             if rh[i] < 1.0:
#                 dp.append((-5321.0 / ((-5.0) - (5321.0 / (273.0 + temp[i])))) - 273.0)
#             else:
#                 dp.append((-5321.0 / ((log(rh[i]/100.0)) - (5321.0 / (273.0 + temp[i])))) - 273.0)

#         return dp

#     @staticmethod
#     def calc_rh(pressure, sphu, temp):
#         """
#         SPHU=0.622*EVAP/PRES         ! specific humidity
#         EVAP=RELH*ESAT               ! vapor pressure
#         ESAT=EXP(21.4-(5351.0/TEMP)) ! saturation vapor pressure

#         rh = EVAP / ESAT = (SPHU * PRES / 0.622) / (EXP(21.4-(5351.0/TEMP)))
#         """
#         if not pressure or not sphu or not temp:
#             return None

#         #rh = []
#         #for i in xrange(len(sphu)):
#         #    print sphu[i], pressure[i], temp[i]
#         #    rh.append((sphu[i] * pressure[i] / 0.622) / (exp(21.4 - (5351.0 / (temp[i] + 273.15)))))

#         return map(lambda s,p,t: (s * p / 0.622) / (exp(21.4 - (5351.0 /(t + 273.15)))), sphu,pressure,temp)
#         #return rh

#     @staticmethod
#     def calc_height(pressure):
#         """
#         height =(Tref/(lapse_rate*0.001))*(1-(pressure/Psfc)^(gas_constant*lapse_rate*0.001/G))
#         """
#         if not pressure:
#             return None

#         P_SURFACE = 1000  # Psfc (mb)
#         T_REF = 288.15    # Tref (K)
#         LAPSE_RATE = 6.5  # Lapse Rate (K/km)
#         G = 9.80665       # Gravitational Constant (m/s*s)
#         Rd = 287.04       # Gas Constant

#         return map(lambda p: (T_REF/(LAPSE_RATE*0.001))*(1.0 - pow(p/P_SURFACE, Rd*LAPSE_RATE*0.001/G)), pressure)




# class Sun(object):
#     """
#     Calculate sunrise and sunset based on equations from NOAA:
#     http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

#     typical use, calculating the sunrise at the present day:

#     from datetime import datetime
#     s = Sun(lat=49,long=3)
#     print s.sunrise(datetime.now())     # prints 'datetime.time(17, 58, 43)'
#     print s.sunrise_hr(datetime.now())  # prints '18'
#     """
#     def __init__(self, lat=52.37, long=4.90):  # default Amsterdam
#         self.lat = lat
#         self.long = long

#     def sunrise(self, when):
#         """
#         Return the time of sunrise as a datetime.time object.
#         when is a datetime.datetime object. If none is given a
#         local time zone is assumed (including daylight saving if present).
#         """
#         self.__preptime(when)
#         self.__calc()
#         return Sun.__timefromdecimalday(self.sunrise_t)

#     def sunrise_hr(self, when):
#         """
#         Return the time of sunrise as an int.
#         when is a datetime.datetime object. If none is given a
#         local time zone is assumed (including daylight saving if present)
#         """
#         self.__preptime(when)
#         self.__calc()
#         return Sun.__hourfromdecimalday(self.sunrise_t)

#     def sunset(self, when):
#         self.__preptime(when)
#         self.__calc()
#         return Sun.__timefromdecimalday(self.sunset_t)

#     def sunset_hr(self, when):
#         self.__preptime(when)
#         self.__calc()
#         return Sun.__hourfromdecimalday(self.sunset_t)

#     def solarnoon(self, when):
#         self.__preptime(when)
#         self.__calc()
#         return Sun.__timefromdecimalday(self.solarnoon_t)

#     @staticmethod
#     def __timefromdecimalday(day):
#         """
#         returns a datetime.time object.
#         day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
#         """
#         hours = 24.0 * day
#         h = int(hours)
#         minutes = (hours - h) * 60
#         m = int(minutes)
#         seconds = (minutes - m) * 60
#         s = int(seconds)
#         return time(hour=h, minute=m, second=s)

#     @staticmethod
#     def __hourfromdecimalday(day):
#         """
#         returns an int representing the hour of a given
#         day as a decimal day between 0.0 and 1.0, e.g. noon = 0.5
#         """
#         hours  = 24.0 * day
#         h = int(hours)
#         minutes= (hours - h) * 60
#         m = int(minutes)
#         return (h + 1) if m > 29 else h

#     def __preptime(self,when):
#         """
#         Extract information in a suitable format from when,
#         a datetime.datetime object.
#         """
#         # datetime days are numbered in the Gregorian calendar
#         # while the calculations from NOAA are distibuted as
#         # OpenOffice spreadsheets with days numbered from
#         # 1/1/1900. The difference are those numbers taken for
#         # 18/12/2010
#         self.day = when.toordinal() - (734124 - 40529)
#         t = when.time()
#         self.time= (t.hour + t.minute / 60.0 + t.second / 3600.0) / 24.0

#         self.timezone = 0
#         offset = when.utcoffset()
#         if not offset is None:
#             self.timezone = offset.seconds / 3600.0

#     def __calc(self):
#         """
#         Perform the actual calculations for sunrise, sunset and
#         a number of related quantities.

#         The results are stored in the instance variables
#         sunrise_t, sunset_t and solarnoon_t
#         """
#         timezone = self.timezone  # in hours, east is positive
#         longitude = self.long     # in decimal degrees, east is positive
#         latitude = self.lat       # in decimal degrees, north is positive

#         time = self.time          # percentage past midnight, i.e. noon  is 0.5
#         day = self.day            # daynumber 1=1/1/1900

#         Jday = day + 2415018.5 + time - timezone / 24  # Julian day
#         Jcent = (Jday - 2451545) / 36525               # Julian century

#         Manom = 357.52911 + Jcent * (35999.05029 - 0.0001537 * Jcent)
#         Mlong = 280.46646 + Jcent * (36000.76983 + Jcent * 0.0003032) % 360
#         Eccent = 0.016708634 - Jcent * (0.000042037 + 0.0001537 * Jcent)
#         Mobliq = 23 + (26 + ((21.448 - Jcent * (46.815 + Jcent * (0.00059 - Jcent * 0.001813)))) / 60) / 60
#         obliq = Mobliq + 0.00256 * cos(rad(125.04 - 1934.136 * Jcent))
#         vary = tan(rad(obliq / 2)) * tan(rad(obliq / 2))
#         Seqcent = sin(rad(Manom))*(1.914602-Jcent*(0.004817+0.000014*Jcent))+sin(rad(2*Manom))*(0.019993-0.000101*Jcent)+sin(rad(3*Manom))*0.000289
#         Struelong = Mlong + Seqcent
#         Sapplong = Struelong - 0.00569 - 0.00478 * sin(rad(125.04 - 1934.136 * Jcent))
#         declination = deg(asin(sin(rad(obliq)) * sin(rad(Sapplong))))

#         eqtime = 4*deg(vary*sin(2*rad(Mlong))-2*Eccent*sin(rad(Manom))+4*Eccent*vary*sin(rad(Manom))*cos(2*rad(Mlong))-0.5*vary*vary*sin(4*rad(Mlong))-1.25*Eccent*Eccent*sin(2*rad(Manom)))

#         hourangle = deg(acos(cos(rad(90.833))/(cos(rad(latitude))*cos(rad(declination)))-tan(rad(latitude))*tan(rad(declination))))

#         self.solarnoon_t = (720 - 4 * longitude - eqtime + timezone * 60) / 1440
#         self.sunrise_t = self.solarnoon_t - hourangle * 4 / 1440
#         self.sunset_t = self.solarnoon_t + hourangle * 4 / 1440
