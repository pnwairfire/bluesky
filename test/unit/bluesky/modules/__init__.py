from bluesky.config import Config

def set_old_consume_defaults():
    # The consume settings defaults changed in v4.4.0, so manually
    # setting them here to the old defaults to get the tests passing

    Config().set({'rx': 5, 'wf': 5, 'other': 5}, 'consumption', 'consume_settings', 'activity','slope','defaults')
    Config().set({'rx': 6, 'wf': 6, 'other': 6}, 'consumption', 'consume_settings', 'activity','windspeed','defaults')
    Config().set({'rx': 10, 'wf': 10, 'other': 10}, 'consumption', 'consume_settings', 'activity','days_since_rain','defaults')
    Config().set({'rx': 50, 'wf': 50, 'other': 50}, 'consumption', 'consume_settings', 'activity','fuel_moisture_10hr_pct','defaults')
    Config().set({'rx': 120, 'wf': 120, 'other': 120}, 'consumption', 'consume_settings', 'activity','length_of_ignition','defaults')
    Config().set({'rx': 'MEAS-Th', 'wf': 'MEAS-Th', 'other': 'MEAS-Th'}, 'consumption', 'consume_settings', 'activity','fm_type','defaults')
    Config().set({'rx': 30,'wf': 30,'other': 30,}, 'consumption', 'consume_settings', 'all', 'fuel_moisture_1000hr_pct', 'defaults')
    Config().set({'rx': 75,'wf': 75,'other': 75,}, 'consumption', 'consume_settings', 'all', 'fuel_moisture_duff_pct', 'defaults')
    Config().set({'rx': 16,'wf': 16,'other': 16,}, 'consumption', 'consume_settings', 'all', 'fuel_moisture_litter_pct', 'defaults')
    Config().set({'rx': 0,'wf': 0,'other': 0,}, 'consumption', 'consume_settings', 'all', 'canopy_consumption_pct', 'defaults')
    Config().set({'rx': 50,'wf': 50,'other': 50,}, 'consumption', 'consume_settings', 'all', 'shrub_blackened_pct', 'defaults')
    Config().set({'rx': 0,'wf': 0,'other': 0,}, 'consumption', 'consume_settings', 'all', 'pile_blackened_pct', 'defaults')
    Config().set({'rx': 100,'wf': 100,'other': 100,}, 'consumption', 'consume_settings', 'all', 'duff_pct_available', 'defaults')
    Config().set({'rx': 100,'wf': 100,'other': 100,}, 'consumption', 'consume_settings', 'all', 'sound_cwd_pct_available', 'defaults')
    Config().set({'rx': 100,'wf': 100,'other': 100,}, 'consumption', 'consume_settings', 'all', 'rotten_cwd_pct_available', 'defaults')
