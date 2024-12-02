"""Unit tests for bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import copy
#from unittest import mock

from numpy import array
from numpy.testing import assert_approx_equal
from pytest import raises

import afconfig

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.modules import emissions

from . import set_old_consume_defaults

FIRES = [
    Fire({
        'source': 'GOES-16',
        'type': "wf",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-04:00",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  0,
                        "specified_points": [
                            {
                                'area': 47.20000000000001,
                                'lat': 50.632,
                                'lng': -71.362,


                                # timeprofile should be ignored and replcaced when running
                                # FRP emissions
                                "timeprofile": {
                                    "2018-06-27T17:00:00": {
                                        'area_fraction': 0.75,
                                        'flaming': 0.75,
                                        'smoldering': 0.3,
                                        'residual': 0.0
                                    },
                                    "2018-06-27T20:00:00": {
                                        'area_fraction': 0.25,
                                        'flaming': 0.25,
                                        'smoldering': 0.7,
                                        'residual': 1.0
                                    }
                                },
                                # Hourly FRP is used for FRP emissions
                                "hourly_frp": {
                                    "2018-06-27T10:00:00": 55.4,
                                    "2018-06-27T11:00:00": 66,
                                    "2018-06-27T12:00:00": 78,
                                    "2018-06-27T13:00:00": 83,
                                    "2018-06-27T18:00:00": 82,
                                    "2018-06-27T19:00:00": 66,
                                    "2018-06-27T20:00:00": 52.5
                                },
                                #55.4 + 66 + 78 + 83 + 82 + 66 + 52.5 = 482.9
                                "frp": 482.9,
                            }
                        ]
                    }
                ]
            }
        ]
    }),
    Fire({
        'type': "rx",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-07:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  0,
                        "specified_points": [
                            {
                                'area': 50.4,
                                'lat': 45.632,
                                'lng': -120.362,
                                #[-120.3, 45.22]

                                "fuelbeds": [
                                    {
                                        "fccs_id": "52",
                                        "pct": 100.0,
                                        "consumption": {
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [200.4],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [900.5],
                                                    "residual": [800.0],
                                                    "flaming": [100.2]
                                                }
                                            },
                                            "ground fuels": {
                                                "duff upper": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [200]
                                                }
                                            }
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    })
]

FIRES_WITH_PILES = [
    Fire({
        'type': "rx",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-07:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  90,
                        "specified_points": [
                            {
                                'area': 50.4,
                                'lat': 45.632,
                                'lng': -120.362,
                                #[-120.3, 45.22]

                                "fuelbeds": [
                                    {
                                        "fccs_id": "52",
                                        "pct": 100.0,
                                        "consumption": {
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [200.4],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [900.5],
                                                    "residual": [800.0],
                                                    "flaming": [100.2]
                                                }
                                            },
                                            "woody fuels": {
                                                "piles": {
                                                    "flaming": [100.0],
                                                    "smoldering": [100.0],
                                                    "residual": [100.0],
                                                }
                                            },
                                            "ground fuels": {
                                                "duff upper": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [200]
                                                }
                                            }
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    })
]

FIRES_WITH_PILES_ONLY = [
    Fire({
        'source': 'GOES-16',
        'type': "wf",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-04:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  90,
                        "specified_points": [
                            {
                                'area': 47.20000000000001,
                                'lat': 50.632,
                                'lng': -71.362,
                                "fuelbeds": [
                                    {
                                        "fccs_id": "52",
                                        "pct": 100.0,
                                        "consumption": {
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            },
                                             "woody fuels": {
                                                "piles": {
                                                    "flaming": [99.16],
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                }
                                            },
                                           "ground fuels": {
                                                "duff upper": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            }
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }),
    Fire({
        'type': "rx",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-07:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  90,
                        "specified_points": [
                            {
                                'area': 50.4,
                                'lat': 45.632,
                                'lng': -120.362,
                                #[-120.3, 45.22]

                                "fuelbeds": [
                                    {
                                        "fccs_id": "53",
                                        "pct": 100.0,
                                        "consumption": {
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            },
                                            "woody fuels": {
                                                "piles": {
                                                    "flaming": [99.16],
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                }
                                            },
                                            "ground fuels": {
                                                "duff upper": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            }
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }),
    Fire({
        'type': "rx",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-07:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  90,
                        "specified_points": [
                            {
                                'area': 50.4,
                                'lat': 45.632,
                                'lng': -120.362,
                                #[-120.3, 45.22]

                                "fuelbeds": [
                                    {
                                        "fccs_id": "0",
                                        "pct": 100.0,
                                        "consumption": {
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            },
                                            "woody fuels": {
                                                "piles": {
                                                    "flaming": [99.16],
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                }
                                            },
                                            "ground fuels": {
                                                "duff upper": {
                                                    "smoldering": [0.0],
                                                    "residual": [0.0],
                                                    "flaming": [0.0]
                                                }
                                            }
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    })
]


CONFIG_FOR_PILE_ONLY_TESTS = {"consumption":{"fuel_loadings":{"foo":{"bar":"baz"},
"52":{"expertFuelbeds":{"1":{"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"percent_of_fire":100,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"","fuelbed_name":"","fuelbed_row":1,"fuel_consumptionEquation":"natural","fccs_number":52000000,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"shrubs_herbs_primary_loading":0,"shrubs_herbs_primary_perc_live":0,"shrubs_herbs_secondary_loading":0,"shrubs_herbs_secondary_perc_live":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":95,"nw_primary_perc_live":70,"nw_secondary_perc_live":80,"shrubs_primary_loading":0,"fuelbed_number":52,"nw_secondary_loading":0,"shrubs_primary_perc_live":89},"2":{},"3":{},"4":{},"5":{}},"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"FB_0052_FCCS.xml","fuelbed_name":"","fuelbed_row":1,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":0,"nw_primary_perc_live":0,"nw_secondary_perc_live":0,"shrubs_primary_loading":0,"fuelbed_number":52,"nw_secondary_loading":0,"shrubs_primary_perc_live":0},
"53":{"expertFuelbeds":{"1":{"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"percent_of_fire":100,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"","fuelbed_name":"","fuelbed_row":1,"fuel_consumptionEquation":"natural","fccs_number":53000000,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"shrubs_herbs_primary_loading":0,"shrubs_herbs_primary_perc_live":0,"shrubs_herbs_secondary_loading":0,"shrubs_herbs_secondary_perc_live":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":95,"nw_primary_perc_live":70,"nw_secondary_perc_live":80,"shrubs_primary_loading":0,"fuelbed_number":53,"nw_secondary_loading":0,"shrubs_primary_perc_live":89},"2":{},"3":{},"4":{},"5":{}},"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"FB_0053_FCCS.xml","fuelbed_name":"","fuelbed_row":1,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":0,"nw_primary_perc_live":0,"nw_secondary_perc_live":0,"shrubs_primary_loading":0,"fuelbed_number":53,"nw_secondary_loading":0,"shrubs_primary_perc_live":0},
"0":{"expertFuelbeds":{"1":{"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"percent_of_fire":100,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"","fuelbed_name":"","fuelbed_row":1,"fuel_consumptionEquation":"natural","fccs_number":0,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"shrubs_herbs_primary_loading":0,"shrubs_herbs_primary_perc_live":0,"shrubs_herbs_secondary_loading":0,"shrubs_herbs_secondary_perc_live":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":95,"nw_primary_perc_live":70,"nw_secondary_perc_live":80,"shrubs_primary_loading":0,"fuelbed_number":0,"nw_secondary_loading":0,"shrubs_primary_perc_live":89},"2":{},"3":{},"4":{},"5":{}},"is_active":True,"Total_available_fuel_loading":99.16,"total_fuels":99.16,"contributed_fuels":11.51,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":0,"duff_upper_loading":0,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"FB_0000_FCCS.xml","fuelbed_name":"","fuelbed_row":1,"ladderfuels_loading":0,"lichen_depth":0,"lichen_loading":0,"litter_depth":0,"litter_loading":0,"midstory_loading":0,"moss_depth":0,"moss_loading":0,"overstory_loading":0,"pile_clean_loading":99.16,"pile_dirty_loading":0,"pile_vdirty_loading":0,"shrubs_needledrape_loading":0,"snags_c1_foliage_loading":0,"snags_c1_wood_loading":0,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0,"snags_c3_loading":0,"squirrel_midden_loading":0,"understory_loading":0,"w_rotten_3_9_loading":0,"w_rotten_9_20_loading":0,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0,"w_sound_1_3_loading":0,"w_sound_3_9_loading":0,"w_sound_9_20_loading":0,"w_sound_gt20_loading":0,"w_sound_quarter_1_loading":0,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0,"w_stump_sound_loading":0,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0,"shrubs_secondary_loading":0,"shrubs_secondary_perc_live":0,"nw_primary_perc_live":0,"nw_secondary_perc_live":0,"shrubs_primary_loading":0,"fuelbed_number":0,"nw_secondary_loading":0,"shrubs_primary_perc_live":0}
}}}


# fb 52 with clean 10, dirty 20, vdirty 30 added
CONFIG_FOR_FB_WITH_PILE_TESTS = {"consumption":{"fuel_loadings":{"foo":{"bar":"baz"},
"52":{"expertFuelbeds":{"1":{"is_active":True,"Total_available_fuel_loading":93.87,"total_fuels":93.87,"contributed_fuels":11.51,"percent_of_fire":100,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":1.1,"duff_upper_loading":7.48,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"","fuelbed_name":"","fuelbed_row":1,"fuel_consumptionEquation":"natural","fccs_number":52000000,"ladderfuels_loading":3,"lichen_depth":0.1,"lichen_loading":0.01,"litter_depth":0.7,"litter_loading":1.88,"midstory_loading":2.84,"moss_depth":0.2,"moss_loading":0.04,"overstory_loading":7.52,"pile_clean_loading":10,"pile_dirty_loading":20,"pile_vdirty_loading":30,"shrubs_needledrape_loading":0,"shrubs_herbs_primary_loading":0.59,"shrubs_herbs_primary_perc_live":79.5,"shrubs_herbs_secondary_loading":0.12,"shrubs_herbs_secondary_perc_live":87.5,"snags_c1_foliage_loading":0.26,"snags_c1_wood_loading":0.94,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0.57,"snags_c3_loading":2.15,"squirrel_midden_loading":0,"understory_loading":0.56,"w_rotten_3_9_loading":0.4,"w_rotten_9_20_loading":2.4,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0.4,"w_sound_1_3_loading":0.4,"w_sound_3_9_loading":0.4,"w_sound_9_20_loading":1.1,"w_sound_gt20_loading":0.6,"w_sound_quarter_1_loading":0.9,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0.25,"w_stump_sound_loading":0.22,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0.2,"shrubs_secondary_loading":0.11,"shrubs_secondary_perc_live":95,"nw_primary_perc_live":70,"nw_secondary_perc_live":80,"shrubs_primary_loading":0.39,"fuelbed_number":52,"nw_secondary_loading":0.01,"shrubs_primary_perc_live":89},"2":{},"3":{},"4":{},"5":{}},"is_active":True,"Total_available_fuel_loading":93.87,"total_fuels":33.87,"contributed_fuels":11.51,"basal_accum_loading":0,"cover_type":118,"duff_lower_depth":0,"duff_lower_loading":0,"duff_upper_depth":1.1,"duff_upper_loading":7.48,"ecoregion":240,"efg_activity":1,"efg_natural":8,"filename":"FB_0052_FCCS.xml","fuelbed_name":"","fuelbed_row":1,"ladderfuels_loading":3,"lichen_depth":0.1,"lichen_loading":0.01,"litter_depth":0.7,"litter_loading":1.88,"midstory_loading":2.84,"moss_depth":0.2,"moss_loading":0.04,"overstory_loading":7.52,"pile_clean_loading":10,"pile_dirty_loading":20,"pile_vdirty_loading":30,"shrubs_needledrape_loading":0,"snags_c1_foliage_loading":0.26,"snags_c1_wood_loading":0.94,"snags_c1wo_foliage_loading":0,"snags_c2_loading":0.57,"snags_c3_loading":2.15,"squirrel_midden_loading":0,"understory_loading":0.56,"w_rotten_3_9_loading":0.4,"w_rotten_9_20_loading":2.4,"w_rotten_gt20_loading":0,"w_sound_0_quarter_loading":0.4,"w_sound_1_3_loading":0.4,"w_sound_3_9_loading":0.4,"w_sound_9_20_loading":1.1,"w_sound_gt20_loading":0.6,"w_sound_quarter_1_loading":0.9,"w_stump_lightered_loading":0,"w_stump_rotten_loading":0.25,"w_stump_sound_loading":0.22,"fuel_lengthOfIgnition":120,"fuel_3MonthHarvest":True,"_id":"","nw_primary_loading":0.295,"shrubs_secondary_loading":0.06,"shrubs_secondary_perc_live":43.75,"nw_primary_perc_live":39.75,"nw_secondary_perc_live":43.75,"shrubs_primary_loading":0.295,"fuelbed_number":52,"nw_secondary_loading":0.06,"shrubs_primary_perc_live":39.75}
}}}


class fire_failure_manager():
    def __init__(self, fire):
        self._fire = fire

    def __enter__(self):
        pass

    def __exit__(self, e_type, value, tb):
        if e_type:
            self._fire['error'] = str(value)
        return True # return true even if there's an error

class BaseEmissionsTest():

    def setup_method(self):
        self.fires = copy.deepcopy(FIRES)
        self.fires_with_piles =copy.deepcopy(FIRES_WITH_PILES)
        self.fires_with_piles_only =copy.deepcopy(FIRES_WITH_PILES_ONLY)

    def _check_emissions(self, expected, actual):
        assert set(expected.keys()) == set(actual.keys())
        for p in expected:
            assert set(expected[p].keys()) == set(actual[p].keys())
            for s in expected[p]:
                assert_approx_equal(expected[p][s][0], actual[p][s][0])

class TestFepsEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'CH4': [1.146763999999999],
            'CO': [21.554359999999996],
            'CO2': [495.23994],
            'NH3': [0.3621612799999999],
            'NOx': [0.7264840000000004],
            'PM10': [2.5788380799999997],
            'PM2.5': [2.1854560000000007],
            'SO2': [0.294196],
            'VOC': [5.206068399999999]
        },
        'residual': {
            'CH4': [9.871947200000001],
            'CO': [210.20404799999997],
            'CO2': [1393.6372320000003],
            'NH3': [3.4119242240000003],
            'NOx': [0.9083631999999999],
            'PM10': [19.633610303999998],
            'PM2.5': [16.6386528],
            'SO2': [0.980392],
            'VOC': [49.04641072000001]
        },
        'smoldering': {
            'CH4': [8.886134000000002],
            'CO': [189.21305999999998],
            'CO2': [1254.46854],
            'NH3': [3.07120928],
            'NOx': [0.817654],
            'PM10': [17.67299688],
            'PM2.5': [14.977116],
            'SO2': [0.88249],
            'VOC': [44.14863340000001]
        },
        'total': {
            'CH4': [19.9048452],
            'CO': [420.97146799999996],
            'CO2': [3143.3457120000003],
            'NH3': [6.845294784],
            'NOx': [2.4525012000000004],
            'PM10': [39.885445264],
            'PM2.5': [33.8012248],
            'SO2': [2.157078],
            'VOC': [98.40111252000001]
        }
    }

    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
            'PM10': [2.5788380799999997],
            'PM2.5': [2.1854560000000007]
        },
        'residual': {
            'PM10': [19.633610303999998],
            'PM2.5': [16.6386528]
        },
        'smoldering': {
            'PM10': [17.67299688],
            'PM2.5': [14.977116]
        },
        'total': {
            'PM10': [39.885445264],
            'PM2.5': [33.8012248]
        }
    }

    def test_wo_details(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")

        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_wo_details_PM_only(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

class TestPrichardOneillEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'CO': [27.028606023103013],
            'SO2': [0.39522236726530535],
            'NOx': [0.5140925],
            'NH3': [0.32721800000000006],
            'CH4': [1.234943344888901],
            'PM2.5': [3.9625206441915526],
            'PM10': [6.223146000000001],
            'CO2': [494.6158285291992]
        },
        'smoldering': {
            'CO': [126.7501603486871],
            'SO2': [1.5593568283333363],
            'NOx': [0.97118925],
            'NH3': [1.6569200000000002],
            'CH4': [6.847284303487535],
            'PM2.5': [17.750671735337],
            'PM10': [18.667365000000004],
            'CO2': [1426.2988355961934]
        },
        'residual': {
            'CO': [0.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [0.0],
            'PM2.5': [0.0],
            'PM10': [0.0],
            'CO2': [0.0]
        },
        'total': {
            'CO': [153.7787663717901],
            'SO2': [1.9545791955986418],
            'NOx': [1.4852817500000002],
            'NH3': [1.9841380000000002],
            'CH4': [8.082227648376435],
            'PM2.5': [21.713192379528554],
            'PM10': [24.890511000000004],
            'CO2': [1920.9146641253924]
        }
    }

    EXPECTED_FIRE52_PILE_ONLY_EMISSIONS = {
        'flaming': {
            'CO': [3289.7123279999996/2000.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [204.90422399999997/2000.0],
            'PM2.5': [843.3558/2000.0],
            'PM10': [968.2973999999999/2000.0],
            'CO2': [214227.366192/2000.0]
        },
        'smoldering': {
            'CO': [1745.211042/2000.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [147.65419799999998/2000.0],
            'PM2.5': [180.7191/2000.0],
            'PM10': [207.49229999999997/2000.0],
            'CO2': [41362.987608/2000.0]
        },
        'residual': {
            'CO': [1745.211042/2000.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [147.65419799999998/2000.0],
            'PM2.5': [180.7191/2000.0],
            'PM10': [207.49229999999997/2000.0],
            'CO2': [41362.987608/2000.0]
        },
        'total': {
            'CO': [6780.134411999999/2000.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [500.2126199999999/2000.0],
            'PM2.5': [1204.794/2000.0],
            'PM10': [1383.282/2000.0],
            'CO2': [296953.341408/2000.0]
        }
    }

    EXPECTED_FIRE_WITH_PILE_EMISSIONS = {
        'flaming': {
            'CO': [28.02388002310301],
            'SO2': [0.39522236726530535],
            'NOx': [0.5140925],
            'NH3': [0.32721800000000006],
            'CH4': [1.296935344888901],
            'PM2.5': [4.3351656441915525],
            'PM10': [6.662571000000001],
            'CO2': [559.4284645291991]
        },
        'smoldering': {
            'CO': [127.2781588486871],
            'SO2': [1.5593568283333363],
            'NOx': [0.97118925],
            'NH3': [1.6569200000000002],
            'CH4': [6.891955803487535],
            'PM2.5': [17.830524235337002],
            'PM10': [18.761527500000003],
            'CO2': [1438.8128495961935]
        },
        'residual': {
            'CO': [0.5279985],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [0.044671499999999996],
            'PM2.5': [0.0798525],
            'PM10': [0.0941625],
            'CO2': [12.514014]
        },
        'total': {
            'CO': [155.83003737179013],
            'SO2': [1.9545791955986418],
            'NOx': [1.4852817500000002],
            'NH3': [1.9841380000000002],
            'CH4': [8.233562648376434],
            'PM2.5': [22.245542379528555],
            'PM10': [25.518261000000003],
            'CO2': [2010.7553281253925]
        }
    }

    SPECIES = ['CH4','CO','CO2','NH3','NOx','PM10','PM2.5','SO2','VOC']

    # Note: no tests with all emissions species, since that would be
    # a huge set

    def test_wo_details_PM_only(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        emissions.PrichardOneill(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        emissions.PrichardOneill(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_pile_only(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        Config().merge(CONFIG_FOR_PILE_ONLY_TESTS)
        emissions.PrichardOneill(fire_failure_manager).run(self.fires_with_piles_only)

        assert 'emissions_details' in self.fires_with_piles_only[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        assert 'emissions_details' in self.fires_with_piles_only[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]

        # first fire
        ed1 = self.fires_with_piles_only[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions_details']
        em1 = self.fires_with_piles_only[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions']
        # second fire
        ed2 = self.fires_with_piles_only[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions_details']
        em2 = self.fires_with_piles_only[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions']

        ## check first fire...
        assert ed1['summary']['total']['flaming']['PM2.5'][0] == em1['flaming']['PM2.5'][0]
        assert ed1['summary']['total']['smoldering']['PM2.5'][0] == em1['smoldering']['PM2.5'][0]
        assert ed1['summary']['total']['residual']['PM2.5'][0] == em1['residual']['PM2.5'][0]
        assert ed1['summary']['total']['total']['PM2.5'][0] == em1['total']['PM2.5'][0]

        # since the only loadings are piles, the woody fuels and piles emissions should match total emissions
        assert ed1['summary']['woody fuels']['flaming']['PM2.5'][0] == em1['flaming']['PM2.5'][0]
        assert ed1['summary']['woody fuels']['smoldering']['PM2.5'][0] == em1['smoldering']['PM2.5'][0]
        assert ed1['summary']['woody fuels']['residual']['PM2.5'][0] == em1['residual']['PM2.5'][0]

        assert ed1['woody fuels']['piles']['flaming']['PM2.5'][0] == em1['flaming']['PM2.5'][0]
        assert ed1['woody fuels']['piles']['smoldering']['PM2.5'][0] == em1['smoldering']['PM2.5'][0]
        assert ed1['woody fuels']['piles']['residual']['PM2.5'][0] == em1['residual']['PM2.5'][0]

        ## check second fire...
        assert ed2['summary']['total']['flaming']['PM2.5'][0] == em2['flaming']['PM2.5'][0]
        assert ed2['summary']['total']['smoldering']['PM2.5'][0] == em2['smoldering']['PM2.5'][0]
        assert ed2['summary']['total']['residual']['PM2.5'][0] == em2['residual']['PM2.5'][0]
        assert ed2['summary']['total']['total']['PM2.5'][0] == em2['total']['PM2.5'][0]

        # since the only loadings are piles, the woody fuels and piles emissions should match total emissions
        assert ed2['summary']['woody fuels']['flaming']['PM2.5'][0] == em2['flaming']['PM2.5'][0]
        assert ed2['summary']['woody fuels']['smoldering']['PM2.5'][0] == em2['smoldering']['PM2.5'][0]
        assert ed2['summary']['woody fuels']['residual']['PM2.5'][0] == em2['residual']['PM2.5'][0]

        assert ed2['woody fuels']['piles']['flaming']['PM2.5'][0] == em2['flaming']['PM2.5'][0]
        assert ed2['woody fuels']['piles']['smoldering']['PM2.5'][0] == em2['smoldering']['PM2.5'][0]
        assert ed2['woody fuels']['piles']['residual']['PM2.5'][0] == em2['residual']['PM2.5'][0]

        # 0 = fb 52 with piles, all other loadings zero
        # 1 = fb 53 with piles, all other loadings zero
        # 2 = fb 0 with piles, all other loadings zero
        # expect (pile) emissions for all to be the same... regardless of fuelbed number
        # because the calculation is done using consume.Emissions which has pile EF (which apply to all fuelbeds)
        # if the piles are calculated in EmissionsCalculator, then the emissions would be different
        self._check_emissions(self.EXPECTED_FIRE52_PILE_ONLY_EMISSIONS,
            self.fires_with_piles_only[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])
        self._check_emissions(self.EXPECTED_FIRE52_PILE_ONLY_EMISSIONS,
            self.fires_with_piles_only[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])
        self._check_emissions(self.EXPECTED_FIRE52_PILE_ONLY_EMISSIONS,
            self.fires_with_piles_only[2]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])


    def test_fb_with_pile_loadings(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        Config().merge(CONFIG_FOR_FB_WITH_PILE_TESTS)
        emissions.PrichardOneill(fire_failure_manager).run(self.fires_with_piles)

        assert 'emissions_details' in self.fires_with_piles[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        ed = self.fires_with_piles[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions_details']
        em = self.fires_with_piles[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions']

        # check that the emissions details match the emissions
        assert ed['summary']['total']['flaming']['PM10'][0] == em['flaming']['PM10'][0]
        assert ed['summary']['total']['flaming']['CO2'][0] == em['flaming']['CO2'][0]
        assert ed['summary']['total']['flaming']['SO2'][0] == em['flaming']['SO2'][0]
        assert ed['summary']['total']['flaming']['NH3'][0] == em['flaming']['NH3'][0]
        assert ed['summary']['total']['flaming']['NOx'][0] == em['flaming']['NOx'][0]
        assert ed['summary']['total']['flaming']['CO'][0] == em['flaming']['CO'][0]
        assert ed['summary']['total']['flaming']['CH4'][0] == em['flaming']['CH4'][0]
        assert ed['summary']['total']['flaming']['PM2.5'][0] == em['flaming']['PM2.5'][0]

        assert ed['summary']['total']['smoldering']['PM2.5'][0] == em['smoldering']['PM2.5'][0]
        assert ed['summary']['total']['residual']['PM2.5'][0] == em['residual']['PM2.5'][0]
        assert ed['summary']['total']['total']['PM2.5'][0] == em['total']['PM2.5'][0]

        # 0 = fb 52 with piles
        self._check_emissions(self.EXPECTED_FIRE_WITH_PILE_EMISSIONS,
            self.fires_with_piles[0]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

class TestConsumeEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'PM': array([0.]),
            'PM10': array([2.77209549]),
            'PM2.5': array([2.49513546]),
            'CO': array([17.01947807]),
            'CO2': array([311.45162419]),
            'CH4': array([0.77762394]),
            'NMHC': array([0.]),
            'NMOC': array([5.09911411]),
            'NH3': array([0.20604391]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.32371577]),
            'SO2': array([0.24886516])
        },
        'smoldering': {
            'PM': array([0.]),
            'PM10': array([3.30220825]),
            'PM2.5': array([2.97228466]),
            'CO': array([21.22384789]),
            'CO2': array([238.82849103]),
            'CH4': array([1.14655256]),
            'NMHC': array([0.]),
            'NMOC': array([4.06743646]),
            'NH3': array([0.27744516]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.16262207]),
            'SO2': array([0.26110856])
        },
        'residual': {
            'PM': array([0.]),
            'PM10': array([1.83502334]),
            'PM2.5': array([1.65168617]),
            'CO': array([11.79400365]),
            'CO2': array([132.71599523]),
            'CH4': array([0.63713447]),
            'NMHC': array([0.]),
            'NMOC': array([2.26025746]),
            'NH3': array([0.15417511]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.0903684]),
            'SO2': array([0.14509694])
        },
        'total': {
            'PM': array([0.]),
            'PM10': array([7.90932708]),
            'PM2.5': array([7.11910629]),
            'CO': array([50.03732961]),
            'CO2': array([682.99611045]),
            'CH4': array([2.56131097]),
            'NMHC': array([0.]),
            'NMOC': array([11.42680803]),
            'NH3': array([0.63766418]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.57670624]),
            'SO2': array([0.65507066])
        }
    }

    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
             'PM10': array([2.772095490888166]),
             'PM2.5': array([2.495135455344884])
        },
        'residual': {
            'PM10': array([1.8350233382047059]),
            'PM2.5': array([1.6516861730015355])
        },
        'smoldering': {
            'PM10': array([3.3022082538727515]),
            'PM2.5': array([2.9722846569511723])
        },
        'total': {
            'PM10': array([7.909327082965625]),
            'PM2.5': array([7.119106285297591])
        }
    }

    def test_wo_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_wo_details_PM_only(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')
        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])
