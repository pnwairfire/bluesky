"""bluesky.extrafilewriters.emissionscsv

Writes fire emissions csv file in the form:

    fire_id,hour,ignition_date_time,date_time,area_fract,flame_profile,smolder_profile,residual_profile,pm25_emitted,pm10_emitted,co_emitted,co2_emitted,ch4_emitted,nox_emitted,nh3_emitted,so2_emitted,voc_emitted,pm25_flame,pm10_flame,co_flame,co2_flame,ch4_flame,nox_flame,nh3_flame,so2_flame,voc_flame,pm25_smold,pm10_smold,co_smold,co2_smold,ch4_smold,nox_smold,nh3_smold,so2_smold,voc_smold,pm25_resid,pm10_resid,co_resid,co2_resid,ch4_resid,nox_resid,nh3_resid,so2_resid,voc_resid,smoldering_fraction,heat,percentile_000,percentile_005,percentile_010,percentile_015,percentile_020,percentile_025,percentile_030,percentile_035,percentile_040,percentile_045,percentile_050,percentile_055,percentile_060,percentile_065,percentile_070,percentile_075,percentile_080,percentile_085,percentile_090,percentile_095,percentile_100
    SF11C38780083219874810,0,201803170000-08:00,201803170000-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.981589,193672.799534,1.937531,2.07856035,2.2195897,2.36061905,2.5016484,2.64267775,2.7837071,2.92473645,3.0657658,3.20679515,3.3478245,3.48885385,3.6298832,3.77091255,3.9119419,4.05297125,4.1940006,4.33502995,4.4760593,4.61708865,4.758118
    SF11C38780083219874810,1,201803170000-08:00,201803170100-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.981589,193672.799534,1.937531,2.0958799,2.2542288,2.4125777,2.5709266,2.7292755,2.8876244,3.0459733,3.2043222,3.3626711,3.52102,3.6793689,3.8377178,3.9960667,4.1544156,4.3127645,4.4711134,4.6294623,4.7878112,4.9461601,5.104509
    SF11C38780083219874810,2,201803170000-08:00,201803170200-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.987726,129115.199689,1.937531,2.04076465,2.1439983,2.24723195,2.3504656,2.45369925,2.5569329,2.66016655,2.7634002,2.86663385,2.9698675,3.07310115,3.1763348,3.27956845,3.3828021,3.48603575,3.5892694,3.69250305,3.7957367,3.89897035,4.002204
    ...
"""

import csv
import logging
import os

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError

class EmissionsCsvWriter(object):

    def __init__(self, dest_dir):
        self._filename = Config.get('extrafiles', 'emissionscsv', 'filename')
        if not self._filename:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'extrafiles' > 'emissionscsv' > 'filename')")
        self._filename = os.path.join(dest_dir, self._filename)

    SPECIES = [
        "PM2.5", "PM10", "CO",  'CO2', 'CH4', 'NOx', 'NH3', 'SO2', 'VOC'
    ]

    # Note: HEADERS contains the columns in the desired output order
    #  (to match the old BlueSky framework output)
    HEADERS = [
        'fire_id', 'hour', 'ignition_date_time', 'date_time', 'area_fract',
        'flame_profile', 'smolder_profile', 'residual_profile'
    ]
    HEADERS.extend([s + '_emitted' for s in SPECIES])
    HEADERS.extend([s + '_flame' for s in SPECIES])
    HEADERS.extend([s + '_smold' for s in SPECIES])
    HEADERS.extend([s + '_resid' for s in SPECIES])
    HEADERS.extend([
        'smoldering_fraction', 'heat'
    ])
    # TODO: are 21 heights columns enough?
    HEADERS.extend(['height_' + str(i) for i in range(21)])

    PIPELINE_PHASES = ('smoldering', 'flaming','residual')
    EMIS_FILE_PHASES = ('smold', 'flame', 'resid')

    def write(self, fires_manager):
        logging.info('Writing emissions csv to %s', self._filename)
        with open(self._filename, 'w', encoding="utf-8") as f:
            self.emissions_writer = csv.writer(f)
            self.emissions_writer.writerow(self.HEADERS)

            for fire in fires_manager.fires:
                with fires_manager.fire_failure_handler(fire):
                    self._write_fire(fire)

    def _write_fire(self, fire):
        if not fire.get('activity'):
            raise ValueError("Activity information required to "
                "write emissions csv")

        for a in fire['activity']:
            self._write_activity(fire, a)

    def _write_activity(self, fire, a):
        if not a.get('timeprofile'):
            raise ValueError("activity timeprofile information "
                "required to write emissions csv")

        # Total emissions values may be in a['emissions'], but
        # we also need per-phase values, so we need the
        # emissions data in the fuelbeds objects
        if not a.get('fuelbeds') or not a['fuelbeds'][0].get('emissions'):
            raise ValueError("activity emissions information "
                "required to write emissions csv")

        for i, ts in enumerate(sorted(list(a.get('timeprofile').keys()))):
            self._write_row(fire, a, i, ts)

    def _write_row(self, fire, a, i, ts):
        tp = a['timeprofile'][ts]
        utc_offset = a['location']['utc_offset'] or 'Z'
        row = {
            "fire_id": fire.get('id', ''),
            "hour": str(i),
            "ignition_date_time": '', # TODO: fill in
            "date_time": ts + utc_offset,
            "area_fract": tp['area_fraction'],
            "flame_profile": tp['flaming'],
            "smolder_profile": tp['smoldering'],
            "residual_profile": tp['residual']
        }

        # Iterate through SPECIES to compute totals
        # by phase; then write out columns in BSF's order
        for s in self.SPECIES:
            if s in a['fuelbeds'][0]['emissions']['total']:
                for f1, f2 in zip(self.PIPELINE_PHASES, self.EMIS_FILE_PHASES):
                    row[s + '_' + f2] = sum([
                        f['emissions'][f1][s][0] for f in a['fuelbeds']
                    ]) * tp[f1]
                row[s + '_emitted'] = sum([row[s + '_' + f2]
                    for f2 in self.EMIS_FILE_PHASES])

        # Note: plumerise might not be defined for the timestamp
        # (e.g. bluesky playground only defines plumerise for the
        #  hours in the dispersion time window)
        if 'plumerise' in g and ts in a['plumerise']:
            pr = a['plumerise'][ts]
            row['smoldering_fraction'] = pr['smolder_fraction']
            for i, h in enumerate(pr['heights']):
                row['height_' + str(i)] = h

        row['heat'] = a['heat']['summary']['total'] * tp['area_fraction']

        self.emissions_writer.writerow(
            [row.get(k, '') for k in self.HEADERS])
