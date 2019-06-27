"""bluesky.extrafilewriters.SMOKEready

Writes smokeready files in the form:

    ¯\\_(ツ)_//¯

"""
import pdb
import os
import logging
from datetime import timedelta, datetime
from afdatetime import parsing as datetime_parsing, timezones

import numpy as np
from bluesky.config import Config
from bluesky import locationutils

class ColumnSpecificRecord(object):
    columndefs = []
    has_newline = True
    
    def __init__(self):
        object.__setattr__(self, "data", dict())

    def __setattr__(self, key, value):
        object.__getattribute__(self, "data")[key] = value

    def __getattr__(self, key):
        if key.startswith('_'):
            raise AttributeError(key)
        return object.__getattribute__(self, "data")[key]

    def __str__(self):
        outstr = ""
        for (fieldlen, name, datatype) in self.columndefs:
            try:
                data = self.data[name]
            except KeyError:
                data = None
            if data is None:
                data = ""
            elif datatype is float:
                if np.isnan(data):
                    data = ""
                elif fieldlen < 5:
                    data = str(int(data))
                elif fieldlen < 8:
                    data = "%5.4f" % data
                else:
                    data = "%8.6f" % data
            else:
                data = str(datatype(data))
            if len(data) > fieldlen:
                data = data[:fieldlen]
            if datatype is str:
                data = data.ljust(fieldlen, ' ')
            else:
                data = data.rjust(fieldlen, ' ')
            outstr += data
        return outstr + (self.has_newline and '\n' or '')

class PTINVRecord(ColumnSpecificRecord):
    has_newline = False
    columndefs = [ (  2, "STID",     int),
                   (  3, "CYID",     int),
                   ( 15, "PLANTID",  str),
                   ( 15, "POINTID",  str),
                   ( 12, "STACKID",  str),
                   (  6, "ORISID",   str),
                   (  6, "BLRID",    str),
                   (  2, "SEGMENT",  str),
                   ( 40, "PLANT",    str),
                   ( 10, "SCC",      str),
                   (  4, "BEGYR",    int),
                   (  4, "ENDYR",    int),
                   (  4, "STKHGT",   float),
                   (  6, "STKDIAM",  float),
                   (  4, "STKTEMP",  float),
                   ( 10, "STKFLOW",  float),
                   (  9, "STKVEL",   float),
                   (  8, "BOILCAP",  float),
                   (  1, "CAPUNITS", str),
                   (  2, "WINTHRU",  float),
                   (  2, "SPRTHRU",  float),
                   (  2, "SUMTHRU",  float),
                   (  2, "FALTHRU",  float),
                   (  2, "HOURS",    int),
                   (  2, "START",    int),
                   (  1, "DAYS",     int),
                   (  2, "WEEKS",    int),
                   ( 11, "THRUPUT",  float),
                   ( 12, "MAXRATE",  float),
                   (  8, "HEATCON",  float),
                   (  5, "SULFCON",  float),
                   (  5, "ASHCON",   float),
                   (  9, "NETDC",    float),
                   (  4, "SIC",      int),
                   (  9, "LATC",     float),
                   (  9, "LONC",     float),
                   (  1, "OFFSHORE", str) ]

class PTINVPollutantRecord(ColumnSpecificRecord):
    has_newline = False
    columndefs = [ ( 13, "ANN",  float),
                   ( 13, "AVD",  float),
                   (  7, "CE",   float),
                   (  3, "RE",   float),
                   ( 10, "EMF",  float),
                   (  3, "CPRI", int),
                   (  3, "CSEC", int) ]

class PTDAYRecord(ColumnSpecificRecord):
    columndefs = [ (  2, "STID",    int),
                   (  3, "CYID",    int),
                   ( 15, "FCID",    str),
                   ( 12, "SKID",    str),
                   ( 12, "DVID",    str),
                   ( 12, "PRID",    str),
                   (  5, "POLID",   str),
                   (  8, "DATE",    str),
                   (  3, "TZONNAM", str),
                   ( 18, "DAYTOT",  float),
                   (  1, "-dummy-", str),
                   ( 10, "SCC",     str) ]

class PTHOURRecord(ColumnSpecificRecord):
    columndefs = [ (  2, "STID",    int),
                   (  3, "CYID",    int),
                   ( 15, "FCID",    str),
                   ( 12, "SKID",    str),
                   ( 12, "DVID",    str),
                   ( 12, "PRID",    str),
                   (  5, "POLID",   str),
                   (  8, "DATE",    str),
                   (  3, "TZONNAM", str),
                   (  7, "HRVAL1",  float),
                   (  7, "HRVAL2",  float),
                   (  7, "HRVAL3",  float),
                   (  7, "HRVAL4",  float),
                   (  7, "HRVAL5",  float),
                   (  7, "HRVAL6",  float),
                   (  7, "HRVAL7",  float),
                   (  7, "HRVAL8",  float),
                   (  7, "HRVAL9",  float),
                   (  7, "HRVAL10", float),
                   (  7, "HRVAL11", float),
                   (  7, "HRVAL12", float),
                   (  7, "HRVAL13", float),
                   (  7, "HRVAL14", float),
                   (  7, "HRVAL15", float),
                   (  7, "HRVAL16", float),
                   (  7, "HRVAL17", float),
                   (  7, "HRVAL18", float),
                   (  7, "HRVAL19", float),
                   (  7, "HRVAL20", float),
                   (  7, "HRVAL21", float),
                   (  7, "HRVAL22", float),
                   (  7, "HRVAL23", float),
                   (  7, "HRVAL24", float),
                   (  8, "DAYTOT",  float),
                   (  1, "-dummy-", str),
                   ( 10, "SCC",     str) ]


class SmokeReadyWriter(object):
  """
  SmokeReadyWriter is an object class that accepts a destination
  dir argument for file location and several kwargs specific to the
  config of the job.
  
  param: dest_dir
  type: str
  """
  def __init__(self, dest_dir, **kwargs):
    # make dynamic to accept args
    self.filedt = datetime.now()

    ptinv = (kwargs.get('ptinv_filename') or
      Config.get('extrafiles', 'smokeready', 'ptinv_filename'))
    ptinv = self.filedt.strftime(ptinv)
    self._ptinv_pathname = os.path.join(dest_dir, ptinv)

    ptday = (kwargs.get('ptday_filename') or
      Config.get('extrafiles', 'smokeready', 'ptday_filename'))
    ptday = self.filedt.strftime(ptday)
    self._ptday_pathname = os.path.join(dest_dir, ptday)

    pthour = (kwargs.get('pthour_filename') or
      Config.get('extrafiles', 'smokeready', 'pthour_filename'))
    pthour = self.filedt.strftime(pthour)
    self._pthour_pathname = os.path.join(dest_dir, pthour)

    separate_smolder = (kwargs.get('separate_smolder') or
      Config.get('extrafiles', 'smokeready', 'separate_smolder'))
    self._separate_smolder = separate_smolder

    write_ptinv_totals = (kwargs.get('write_ptinv_totals') or
      Config.get('extrafiles', 'smokeready', 'write_ptinv_totals'))
    self._write_ptinv_totals = write_ptinv_totals

    write_ptday_file = (kwargs.get('write_ptday_file') or
      Config.get('extrafiles', 'smokeready', 'write_ptday_file'))
    self._write_ptday_file = write_ptday_file

  # main write function to be called
  def write(self, fires_manager):
    fires_info = fires_manager.fires
    country_process_list = ['US', 'USA', 'United States']

    ptinv = open(self._ptinv_pathname, 'w')
    ptday = open(self._ptday_pathname, 'w')
    pthour = open(self._pthour_pathname, 'w')

    ptinv.write("#IDA\n#PTINV\n#COUNTRY %s\n" % country_process_list[0])
    ptinv.write("#YEAR %d\n" % self.filedt.year)
    ptinv.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")
    ptinv.write("#DATA PM2_5 PM10 CO NH3 NOX SO2 VOC\n")

    ptday.write("#EMS-95\n#PTDAY\n#COUNTRY %s\n" % country_process_list[0])
    ptday.write("#YEAR %d\n" % self.filedt.year)
    ptday.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

    pthour.write("#EMS-95\n#PTHOUR\n#COUNTRY %s\n" % country_process_list[0])
    pthour.write("#YEAR %d\n" % self.filedt.year)
    pthour.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

    num_of_fires = 0
    skip_no_emiss = 0
    skip_no_plume = 0
    skip_no_country = 0
    total_skipped = 0

    for fire_info in fires_info:
      for fire_loc in fire_info.locations:

        if fire_loc["emissions"] is None:
          skip_no_emiss += 1
          total_skipped += 1
          continue

        if fire_loc["plumerise"] is None:
          skip_no_plume += 1
          total_skipped += 1
          continue

        if fire_loc['country'] not in country_process_list:
          skip_no_country += 1
          total_skipped += 1
          continue

        lat, lng = fire_loc["lat"], fire_loc["lng"]
        cyid, stid = self._get_state_county_fips(lat, lng)
        scc = self._map_scc(fire_info.type)
        start_dt =  datetime_parsing.parse(fire_loc['start'])
        start_hour = start_dt.hour

        # if timeprofile key has 0 values, (for flaming/resid/etc), do we
        # ignore or still right the value. 
        num_hours = len(fire_loc['timeprofile'].keys())
        num_days = num_hours // 24
        if num_hours % 24 > 0: num_days += 1
        fcid = self._generate_fcid(start_dt, num_hours, lat, lng)
        tzonnam = self._set_timezone_name(lat, lng, start_dt)

        
        # timedelta
        # sorted(fire_loc['timeprofile'].keys())

        """
          Define fire types, defaults to total. 
          NOTE: flame/smolder were changed to flaming/smoldering
          to be used as keys in the fire_loc['fuelbeds']['emissions'] arr
        """
        if self._separate_smolder:
            fire_types = ("flaming", "smoldering")
        else:
            fire_types = ("total",)

        # iterate through fire_types
        for fire_type in fire_types:
          if fire_type == "total":
              ptid = '1'                 # Point ID
              skid = '1'                 # Stack ID
          elif fire_type == "flaming":
              ptid = '1'                       # Point ID
              skid = '1'                       # Stack ID
              scc = scc[:-2] + "F" + scc[-1]
          elif fire_type == "smoldering":
              ptid = '2'                       # Point ID
              skid = '2'                       # Stack ID
              scc = scc[:-2] + "S" + scc[-1]
          prid = ''                       # Process ID

          # Does the old fireLoc['date_time'] == ['start'] ?
          # dt = fireLoc['date_time']

          date = start_dt.strftime('%m/%d/%y')  # Date
          

          # PTINVRecord
          ptinv_rec = PTINVRecord()
          ptinv_rec.STID = stid
          ptinv_rec.CYID = cyid
          ptinv_rec.PLANTID = fcid
          ptinv_rec.POINTID = ptid
          ptinv_rec.STACKID = skid
          ptinv_rec.SCC = scc
          ptinv_rec.LATC = lat
          ptinv_rec.LONC = lng

          pdb.set_trace()
          ptinv_rec_str = str(ptinv_rec)

          EMISSIONS_MAPPING = [('PM2_5', 'pm2.5'),
                              ('PM10', 'pm10'),
                              ('CO', 'co'),
                              ('NH3', 'nh3'),
                              ('NOX', 'nox'),
                              ('SO2', 'so2'),
                              ('VOC', 'voc')]

          if self._write_ptinv_totals:
            for var, vkey in EMISSIONS_MAPPING:
              for fuelbed in fire_loc['fuelbeds']:
                if fuelbed['emissions'][fire_type][vkey.upper()] is None:
                  continue
                prec = PTINVPollutantRecord()
                prec.ANN = fuelbed['emissions'][fire_type][vkey.upper()][0]
                prec.AVD = fuelbed['emissions'][fire_type][vkey.upper()][0]
                ptinv_rec_str += str(prec)

          ptinv.write(ptinv_rec_str + "\n")

          if self._write_ptday_file:
            for var, vkey in EMISSIONS_MAPPING:
              for fuelbed in fire_loc['fuelbeds']:
                if fuelbed['emissions'][fire_type][vkey.upper()] is None:
                  continue
                for day in range(num_days):
                  dt = start_dt + timedelta(days=day)
                  date = dt.strftime('%m/%d/%y')
                  
                  # PTDAYRecord
                  ptday_rec = PTDAYRecord()
                  ptday_rec.STID = stid
                  ptday_rec.CYID = cyid
                  ptday_rec.FCID = fcid
                  ptday_rec.SKID = ptid
                  ptday_rec.DVID = skid
                  ptday_rec.PRID = prid
                  ptday_rec.POLID = var
                  ptday_rec.DATE = date
                  ptday_rec.TZONNAM = tzonnam

                  start_slice = max((24 * d) - start_hour, 0)
                  end_slice = min((24 * (d + 1)) - start_hour, len(fireLoc["emissions"][vkey]))

          

  def _write_ptinv_file(self):
    ptinv = open(self._ptinv_pathname, 'w')
    ptinv.write("#IDA\n#PTINV\n#COUNTRY %s\n" % country_process_list[0])
    ptinv.write("#YEAR %d\n" % self.filedt.year)
    ptinv.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")
    ptinv.write("#DATA PM2_5 PM10 CO NH3 NOX SO2 VOC\n")

  def _write_ptday_file(self):
    ptday = open(self._ptday_pathname, 'w')
    ptday.write("#EMS-95\n#PTDAY\n#COUNTRY %s\n" % country_process_list[0])
    ptday.write("#YEAR %d\n" % self.filedt.year)
    ptday.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

  def _write_pthour_file(self):
    pthour = open(self._pthour_pathname, 'w')
    pthour.write("#EMS-95\n#PTHOUR\n#COUNTRY %s\n" % country_process_list[0])
    pthour.write("#YEAR %d\n" % self.filedt.year)
    pthour.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

  def _get_state_county_fips(self, lat, lng):
    fips = locationutils.Fips(lat, lng)
    return fips.county_fips, fips.state_fips

  def _map_scc(self, fire_type):
    # Mappings provided by BSF (fill_data.py)
    SCC_CODE_MAPPING = {
        "wildfires": "2810001000",
        "wildfire": "2810001000",
        "wf": "2810001000",
        "rx": "2810015000",
        "unknown": "2810090000"
    }

    if type(fire_type) is str:
      try:
        return SCC_CODE_MAPPING[fire_type]
      except:
        raise ValueError("Invalid Fire Type {}".format(fire_type))
    else:
      raise ValueError("Fire Type must be a string")

  # confirm this is necessary to be like in BSF. Couldnt understand where id was
  # being set. not sure it corresponds to something we need
  def _generate_fcid(self, start_dt, num_hours, lat, lng):
    dt_str = start_dt.strftime('%Y%m%d_')
    lat_str = str(lat).replace('.', '')
    lng_str = str(lng).replace('.', '')

    return dt_str + str(num_hours) + lat_str + lng_str

  def _set_timezone_name(self, lat, lng, start_dt):
    VALID_TIMEZONES = ['GMT','ADT','AST','EDT','EST','CDT','CST','MDT','MST','PDT','PST','AKDT', 'AKST']
          
    try:
      dst_obj = timezones.DstAccurateTimeZone().find(lat, lng, start_dt)
      tzonnam = dst_obj['abbreviation']
      
      if dst_obj['abbreviation'] == 'UTC':
        tzonnam = 'GMT'

      if tzonnam not in VALID_TIMEZONES:
        offset = timezones.UtcOffsetFinder().find(lng, lat, start_dt)[1]
        offset = abs(int(offset.split(':')[0]))
        tzonnam = ['EST','CST','MST','PST', 'AKST'][tzoffset - 5]

      return tzonnam

    except:
      # Default to 'EST' if all else fails
      tzonnam = 'EST'
      return tzonnam


