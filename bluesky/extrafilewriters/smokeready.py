"""bluesky.extrafilewriters.smokeready

Writes three SMOKE Ready File Formats
- PTINV
- PTDAY
- PTHOUR

Documentation for file
formats provided by the CMAS center at https://www.cmascenter.org/smoke/documentation/3.5/html/ch08s02.html.

Functionality and some methods were ported from the Bluesky-Framework repository.
The script used as the source for this can be found here:
https://github.com/pnwairfire/bluesky-framework/blob/e813cb6d01fb41149ec07b176d24acb5eeab6222/src/base/modules/smoke.py
"""

import os
import logging
from datetime import timedelta, datetime
from afdatetime import parsing as datetime_parsing, timezones
import numpy as np
from bluesky.config import Config
from bluesky import locationutils
from bluesky.exceptions import BlueSkyConfigurationError
from hashlib import blake2b

class ColumnSpecificRecord():
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
                try:
                  data = str(datatype(data))
                except:
                  logging.debug('Error setting data at name %s', name)
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


class SmokeReadyWriter():
  """
  SmokeReadyWriter is an object class that accepts a destination
  dir argument for file location and several kwargs specific to the
  config of the job.

  param: dest_dir
  type: str

  configurable kwargs set in the config block:
    defaults:
      "ptinv_filename": "ptinv-%Y%m%d%H.ida",
      "ptday_filename": "ptday-%Y%m%d%H.ems95",
      "pthour_filename": "pthour-%Y%m%d%H.ems95",
      "separate_smolder": true,
      "write_ptinv_totals": true,
      "write_ptday_file": true

  config can be seen in ./dev/config/extrafiles/smokeready.json
  """
  def __init__(self, dest_dir, **kwargs):
    ptinv = (kwargs.get('ptinv_filename') or
      Config().get('extrafiles', 'smokeready', 'ptinv_filename'))
    self._ptinv_pathname = os.path.join(dest_dir, ptinv)

    ptday = (kwargs.get('ptday_filename') or
      Config().get('extrafiles', 'smokeready', 'ptday_filename'))
    self._ptday_pathname = os.path.join(dest_dir, ptday)

    pthour = (kwargs.get('pthour_filename') or
      Config().get('extrafiles', 'smokeready', 'pthour_filename'))
    self._pthour_pathname = os.path.join(dest_dir, pthour)

    separate_smolder = (kwargs.get('separate_smolder') or
      Config().get('extrafiles', 'smokeready', 'separate_smolder'))
    self._separate_smolder = separate_smolder

    write_ptinv_totals = (kwargs.get('write_ptinv_totals') or
      Config().get('extrafiles', 'smokeready', 'write_ptinv_totals'))
    self._write_ptinv_totals = write_ptinv_totals

    write_ptday_file = (kwargs.get('write_ptday_file') or
      Config().get('extrafiles', 'smokeready', 'write_ptday_file'))
    self._write_ptday_file = write_ptday_file

    try:
      use_fips = (kwargs.get('use_fips') or Config().get('extrafiles', 'smokeready', 'use_fips'))
      self._use_fips = use_fips
    except:
      self._use_fips = False

    # Pull the file year out of the dynamically set timestamp
    try:
      self.file_year = int(pthour.split('-')[1][:4])
    except Exception as e:
      logging.debug('Error parsing PT filenames')
      logging.debug(e)
      raise BlueSkyConfigurationError("Improperly formatted PT Filename: use YYYYMMDDHH filename format.")

  # main write function to be called
  def write(self, fires_manager):
    fires_info = fires_manager.fires
    country_process_list = ['US', 'USA', 'United States']

    ptinv = open(self._ptinv_pathname, 'w')
    ptday = open(self._ptday_pathname, 'w')
    pthour = open(self._pthour_pathname, 'w')

    ptinv.write("#IDA\n#PTINV\n#COUNTRY %s\n" % country_process_list[0])
    ptinv.write("#YEAR %d\n" % self.file_year)
    ptinv.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")
    ptinv.write("#DATA PM2_5 PM10 CO NH3 NOX SO2 VOC PTOP PBOT LAY1F\n")

    ptday.write("#EMS-95\n#PTDAY\n#COUNTRY %s\n" % country_process_list[0])
    ptday.write("#YEAR %d\n" % self.file_year)
    ptday.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

    pthour.write("#EMS-95\n#PTHOUR\n#COUNTRY %s\n" % country_process_list[0])
    pthour.write("#YEAR %d\n" % self.file_year)
    pthour.write("#DESC POINT SOURCE BlueSky Framework Fire Emissions\n")

    num_of_fires = 0
    skip_no_lat_lng = 0
    skip_no_emiss = 0
    skip_no_lat_lng = 0
    skip_no_plume = 0
    skip_bad_fips = 0
    total_skipped = 0

    for fire_info in fires_info:
      with fires_manager.fire_failure_handler(fire_info):
       for fire_loc in fire_info.locations:

        # Use locationutils.LatLng rather than just look for 'lat' and 'lng'
        #  keys in order to support both specified points and perimeters
        try:
          lat_lng = locationutils.LatLng(fire_loc)
        except:
          skip_no_lat_lng += 1
          total_skipped += 1
          continue

        num_of_fires += 1
        if "emissions" not in fire_loc.keys():
          skip_no_emiss += 1
          total_skipped += 1
          continue

        if "plumerise" not in fire_loc.keys():
          skip_no_plume += 1
          total_skipped += 1
          continue

        lat, lng = lat_lng.latitude, lat_lng.longitude

        emissions = self._get_location_emissions(fire_loc)

        # try to get CYID/STID, but skip record if lat/lng invalid
        try:
          cyid, stid = self._get_state_county_fips(lat=lat, lng=lng, use_fips=self._use_fips)
        except ValueError:
          invalid = "Invalid Lat:%s and/or Invalid Lng:%s when pulling FIPs Code" % (lat, lng)
          logging.debug(invalid)
          skip_bad_fips += 1
          total_skipped += 1
          continue

        scc = self._map_scc(fire_info.type)
        start_dt =  datetime_parsing.parse(fire_loc['start'])
        start_hour = start_dt.hour

        # if timeprofile key has 0 values, (for flaming/resid/etc), do we
        # ignore or still right the value.
        num_hours = len(fire_loc['timeprofile'].keys())
        num_days = num_hours // 24
        if num_hours % 24 > 0: num_days += 1
        fcid = self._generate_fcid(fire_info, num_hours, lat, lng)

        """
        NOTE: In the old BSF runs, timezone was never
        operational, and defaulted to EST in every output I reviewed.
        Per https://www.cmascenter.org/smoke/documentation/2.7/html/ch02s09s14.html,
        the timezone field is only used if timezone cannot be determined through FIPS code.
        """
        tzonnam = self._set_timezone_name(lat, lng, start_dt)


        # Define fire types, defaults to total.
        if self._separate_smolder:
            fire_phases = ("flaming", "smoldering")
        else:
            fire_phases = ("total",)

        # iterate through fire_phases
        for fire_phase in fire_phases:
          if fire_phase == "total":
              ptid = '1'                 # Point ID
              skid = '1'                 # Stack ID
          elif fire_phase == "flaming":
              ptid = '1'                       # Point ID
              skid = '1'                       # Stack ID
              scc = scc[:-2] + "F" + scc[-1]
          elif fire_phase == "smoldering":
              ptid = '2'                       # Point ID
              skid = '2'                       # Stack ID
              scc = scc[:-2] + "S" + scc[-1]
          prid = ''                       # Process ID

          date = start_dt.strftime('%m/%d/%y')  # Date

          EMISSIONS_MAPPING = [('PM2_5', "pm2.5"),
                              ('PM10', "pm10"),
                              ('CO', "co"),
                              ('NH3', "nh3"),
                              ('NOX', "nox"),
                              ('SO2', "so2"),
                              ('VOC', "voc")]

          """
          PTINV
          """
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

          ptinv_rec_str = str(ptinv_rec)

          if self._write_ptinv_totals:
            logging.debug('Writing SmokeReady PTINV File to %s', self._ptinv_pathname)
            for var, vkey in EMISSIONS_MAPPING:
                if vkey.upper() in emissions[fire_phase]:
                  if emissions[fire_phase][vkey.upper()] is None:
                    continue
                  prec = PTINVPollutantRecord()
                  val = emissions[fire_phase][vkey.upper()]
                  if fire_phase == 'smoldering':
                    val += emissions['residual'][vkey.upper()]
                  prec.ANN = val
                  prec.AVD = val
                  ptinv_rec_str += str(prec)

          ptinv.write(ptinv_rec_str + "\n")

          """
          PTDAY
          """
          if self._write_ptday_file:
            logging.debug('Writing SmokeReady PTHOUR File to %s', self._ptday_pathname)
            for var, vkey in EMISSIONS_MAPPING:
                if vkey.upper() in emissions[fire_phase]:
                  if emissions[fire_phase][vkey.upper()] is None:
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

                    if fire_phase == "smoldering":
                      daytot = emissions[fire_phase][vkey.upper()] + emissions['residual'][vkey.upper()]
                    else:
                      daytot = emissions[fire_phase][vkey.upper()]

                    ptday_rec.DAYTOT = daytot                # Daily total
                    ptday_rec.SCC = scc                      # Source Classification Code
                    ptday.write(str(ptday_rec))

          """
          PTHOUR
          """
          PTHOUR_MAPPING = [('PTOP', "percentile_100"),
                            ('PBOT', "percentile_000"),
                            ('LAY1F', "smoldering_fraction"),
                            ('PM2_5', "pm2.5"),
                            ('PM10', "pm10"),
                            ('CO', "co"),
                            ('NH3', "nh3"),
                            ('NOX', "nox"),
                            ('SO2', "so2"),
                            ('VOC', "voc")]

          logging.debug('Writing SmokeReady PTHOUR File to %s', self._pthour_pathname)
          for var, vkey in PTHOUR_MAPPING:
            species_key = vkey.upper()

            if var in ('PTOP', 'PBOT', 'LAY1F'):
              if fire_loc['plumerise'] is None: continue
            else:
              if species_key not in emissions['total'].keys(): continue

            # collect sorted hour list
            ordered_hours = sorted(fire_loc['plumerise'].keys())

            for day in range(num_days):
                dt = start_dt + timedelta(days=day)
                date = dt.strftime('%m/%d/%y')  # Date

                # PTHOUR Record
                pthour_rec = PTHOURRecord()
                pthour_rec.STID = stid
                pthour_rec.CYID = cyid
                pthour_rec.FCID = fcid
                pthour_rec.SKID = ptid
                pthour_rec.DVID = skid
                pthour_rec.PRID = prid
                pthour_rec.POLID = var
                pthour_rec.DATE = date
                pthour_rec.TZONNAM = tzonnam
                pthour_rec.SCC = scc

                daytot = 0.0
                for hour in range(24):
                  h = (day * 24) + hour - start_hour
                  if h < 0:
                    setattr(pthour_rec, 'HRVAL' + str(hour+1), 0.0)
                    continue
                  try:
                    plumerise_hour = fire_loc['plumerise'][ordered_hours[h]]
                    timeprofile_hour = fire_loc['timeprofile'][ordered_hours[h]]
                    emissions_summary = fire_loc['emissions']['summary']

                    if var in ('PTOP', 'PBOT', 'LAY1F'):
                      if fire_phase == "flaming":
                        if var == 'LAY1F':
                          value = 0.0001
                        elif var == 'PTOP':
                          value = plumerise_hour['heights'][-1]
                        elif var == 'PBOT':
                          value = plumerise_hour['heights'][0]
                        else:
                          value = None
                      elif fire_phase == "smoldering":
                        value = {'LAY1F': 1.0, 'PTOP': 0.0, 'PBOT': 0.0}[var]
                      else:
                        if var == 'LAY1F':
                          value = plumerise_hour['smoldering_fraction']
                        elif var == 'PTOP':
                          value = plumerise_hour['heights'][-1]
                        elif var == 'PBOT':
                          value = plumerise_hour['heights'][0]
                        else:
                          value == None
                    else:
                      if fire_phase == "flaming":
                        flaming_total = emissions[fire_phase][species_key]
                        value = (timeprofile_hour[fire_phase] * flaming_total)
                      elif fire_phase == "smoldering":
                        smoldering_total = emissions[fire_phase][species_key]
                        residual_total = emissions['residual'][species_key]
                        smoldering_value = (timeprofile_hour[fire_phase] * smoldering_total)
                        residual_value = (timeprofile_hour['residual'] * residual_total)
                        # smoke wants smoldering + residual
                        value = smoldering_value + residual_value
                      else:
                        # fallback to total
                        if species_key in emissions_summary.keys():
                          value = emissions_summary[species_key]
                      daytot += value
                    setattr(pthour_rec, 'HRVAL' + str(hour+1), value)
                  except IndexError as e:
                          logging.debug("IndexError on hour %d for fire" % (h))
                          setattr(pthour_rec, 'HRVAL' + str(hour+1), 0.0)

                if var not in ('PTOP', 'PBOT', 'LAY1F'):
                  pthour_rec.DAYTOT = daytot
                pthour.write(str(pthour_rec))
    # Close Files
    ptinv.close()
    if self._write_ptday_file:
      ptday.close()
    pthour.close()
    logging.debug("SmokeReady Process Complete.")
    logging.debug(" #FIRES: %s", num_of_fires)
    logging.debug(" #SKIPPED: %s", total_skipped)
    logging.debug(" #NO LAT/LNG: %s", skip_no_lat_lng)
    logging.debug(" #NO EMISS: %s", skip_no_emiss)
    logging.debug(" #NO PLUME: %s", skip_no_plume)
    logging.debug(" #BAD FIPS: %s", skip_bad_fips)


  def _get_location_emissions(self, fire_loc):
    """Emissions are recored per phase at the fuelbed level, but only
    totals are specified at the location level.  We need them per phase
    at the location level
    """
    emissions = {}
    for fuelbed in fire_loc['fuelbeds']:
      for phase in fuelbed['emissions']:
        emissions[phase] = emissions.get(phase) or {}
        for species in fuelbed['emissions'][phase]:
          species_upper = species.upper()
          emissions[phase][species_upper] = emissions[phase].get(species_upper) or 0.0
          emissions[phase][species_upper] += fuelbed['emissions'][phase][species][0]
    return emissions


  def _get_state_county_fips(self, lat, lng, use_fips=False):
    """
      CMAS has a State/County FIPS code that is 5 digits long. Country Code is appened to make the 6-digit SMOKE code.
      Please refer to the documentation here:
      https://www.cmascenter.org/smoke/documentation/3.7/html/ch02s03s04.html

      Per 04/06/2021 -- we've determined FIPS lookup to be nonessential for our purposes
      so this function will return a defualt value.
    """
    if not use_fips:
      logging.debug("Using a default FIPS code")
      cyid = '221'
      stid = '13'
    else:
      logging.debug("Looking up FIPS code for each fire location")
      fips = locationutils.Fips(lat, lng)
      cyid = fips.county_fips[2:].lstrip('0')
      stid = fips.state_fips.lstrip('0')
    return cyid, stid

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

  # This is how the PTINV file links back to the ptday/pthour emissions files
  # to create a "unique" id, the larger cat'd string w/fsid,lat,lon,hours is
  # converted to hash. hopefully, that doesn't result in too many collisions
  # but it has to be better than relying on the first 15 chars of the below
  def _generate_fcid(self, fire_info, num_hours, lat, lng):
    # Returns the fire_info id, lat/lng, and num of hours burning
    lat_str = str(lat).replace('.', '')
    lng_str = str(lng).replace('.', '')
    fcid_str = fire_info.id + lat_str + lng_str + str(num_hours)
    return blake2b(fcid_str.encode(),digest_size=7).hexdigest()

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
