"""bluesky.outputter.emissionscsv

Writes fire emissions csv file in the form:

  fire_id,hour,ignition_date_time,date_time,area_fract,flame_profile,smolder_profile,residual_profile,pm25_emitted,pm10_emitted,co_emitted,co2_emitted,ch4_emitted,nox_emitted,nh3_emitted,so2_emitted,voc_emitted,pm25_flame,pm10_flame,co_flame,co2_flame,ch4_flame,nox_flame,nh3_flame,so2_flame,voc_flame,pm25_smold,pm10_smold,co_smold,co2_smold,ch4_smold,nox_smold,nh3_smold,so2_smold,voc_smold,pm25_resid,pm10_resid,co_resid,co2_resid,ch4_resid,nox_resid,nh3_resid,so2_resid,voc_resid,smoldering_fraction,heat,percentile_000,percentile_005,percentile_010,percentile_015,percentile_020,percentile_025,percentile_030,percentile_035,percentile_040,percentile_045,percentile_050,percentile_055,percentile_060,percentile_065,percentile_070,percentile_075,percentile_080,percentile_085,percentile_090,percentile_095,percentile_100
  SF11C409055316036814940,0,201804080000-07:00,201804080000-07:00,0.0057,0.0057,0.0057,0.0057,0.002013,0.002376,0.020651,0.415206,0.001076,0.00059,0.000345,0.000249,0.004958,0.001726,0.002037,0.017024,0.391157,0.000906,0.000574,0.000286,0.000232,0.004112,0.000287,0.000339,0.003627,0.024049,0.00017,1.6e-05,5.9e-05,1.7e-05,0.000846,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.963178,102233.839422,3.874123,4.06782915,4.2615353,4.45524145,4.6489476,4.84265375,5.0363599,5.23006605,5.4237722,5.61747835,5.8111845,6.00489065,6.1985968,6.39230295,6.5860091,6.77971525,6.9734214,7.16712755,7.3608337,7.55453985,7.748246
  ...
"""

class EmissionsCsvOutputter(object):

    def __init__(self, **config):
        super(EmissionsCsvOutputter, self).__init__(extra_exports, **config)
        self._output_file = self.config('output_file')
        if not self._output_file:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'output' > 'emissionscsv' > 'output_file')")
        # Note: _bundle will create self._dest if it doesn't exist


    def output(self, fires_manager):
        logging.info('Saving locally to %s', self._output_file)
        with open(self._output_file, 'w') as f:
            emissions_writer = csv.writer(csvfile)
            # TODO: only include plume rise columns if plumerise
            #   has already been calcualted
            emissions_writer.writerow([]) # write header row
            for fire in fires_manager.fires:
                emissions_writer.writerow([])
