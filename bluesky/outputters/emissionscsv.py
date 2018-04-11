"""bluesky.outputter.emissionscsv

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

from bluesky.exceptions import BlueSkyConfigurationError

class EmissionsCsvOutputter(object):

    def __init__(self, **config):
        self._output_file = config.get('output_file')
        if not self._output_file:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'output' > 'emissionscsv' > 'output_file')")

    SPECIES = [
        "PM2.5", "PM10", "CO",  'CO2', 'CH4', 'NOX', 'NH3', 'SO2', 'VOC'
    ]
    def output(self, fires_manager):
        self._make_output_dir()

        logging.info('Saving emissions csv output to %s', self._output_file)
        with open(self._output_file, 'w') as f:
            emissions_writer = csv.writer(f)
            # Write header row
            # TODO: only include plume rise columns if plumerise
            #   has already been calcualted
            headers = [
                'fire_id',
                'hour',
                'ignition_date_time',
                'date_time',
                'area_fract',
                'flame_profile',
                'smolder_profile',
                'residual_profile'
            ]
            headers.extend([s + '_emitted' for s in self.SPECIES])
            headers.extend([s + '_flame' for s in self.SPECIES])
            headers.extend([s + '_smold' for s in self.SPECIES])
            headers.extend([s + '_resid' for s in self.SPECIES])
            headers.extend([
                'smoldering_fraction', 'heat'
            ])

            # TODO: determine number of heights from first fire
            headers.extend(['height_' + str(i) for i in range(21)])
            emissions_writer.writerow(headers)


            for fire in fires_manager.fires:
                with fires_manager.fire_failure_handler(fire):
                    if not fire.get('growth'):
                        raise ValueError("Growth information required to "
                            "output emissions csv")

                    for g in fire['growth']:
                        if not g.get('timeprofile'):
                            raise ValueError("growth timeprofile information "
                                "required to output emissions csv")
                        if not g.get('emissions'):
                            raise ValueError("growth emissions information "
                                "required to output emissions csv")
                        for i, ts in enumerate(sorted(list(g.get('timeprofile').keys()))):
                            row = [
                                fire.get('id', ''),
                                str(i),
                                '', # TODO: fill in ignition_date_time
                                ts,
                                g['timeprofile'][ts]['area_fraction'],
                                g['timeprofile'][ts]['flaming'],
                                g['timeprofile'][ts]['smoldering'],
                                g['timeprofile'][ts]['residual']
                            ]

                            # TODO: '_emitted' species fields
                            # TODO: '_flame' species fields
                            # TODO: '_smold' species fields
                            # TODO: '_resid' species fields
                            # TODO: smoldering_fraction
                            # TODO: timeprofiled heat ???
                            #    row.append(g['heat']['summary']['total'])
                            # TODO: plume heights

                            emissions_writer.writerow(row)

    def _make_output_dir(self):
        output_dir = os.path.dirname(self._output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
