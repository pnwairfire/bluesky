"""Unit tests for bluesky.modules.emissions"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import copy

from py.test import raises

from bluesky.models.fires import Fire
from bluesky.modules import emissions

PERIMETER = {
    "type": "MultiPolygon",
    "coordinates": [
        [
            [
                [-84.8194, 30.5222],
                [-84.8197, 30.5209],
                # ...add more coordinates...
                [-84.8193, 30.5235],
                [-84.8194, 30.5222]
            ]
        ]
    ]
}

##
## Tests for summarize
##

class TestSummarize(object):

    def test_no_fires(self):
        assert emissions.summarize([]) == {}

    def test_one_fire_one_fuelbed(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": {"CO": [1.0]},
                                    "smoldering": {"CO": [2.0]},
                                    "total": {"CO": [3.0]}
                                },
                                "midstory": {
                                    "flaming": {"CO": [4.0]},
                                    "residual": {"CO2": [4.0]}
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": {"CO": [5.0]}
                                }
                            }
                        }
                    }
                ]
            })
        ]
        assert emissions.summarize(fires) == fires[0]['fuelbeds'][0]['emissions']

    def test_one_fire_two_fuelbeds(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": {"CO": [1.0]},
                                    "smoldering": {"CO": [2.0]},
                                    "total": {"CO": [3.0]}
                                },
                                "midstory": {
                                    "flaming": {"CO": [4.0]},
                                    "residual": {"CO2": [4.0]}
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": {"CO": [5.0]}
                                }
                            }
                        }
                    },
                    {
                        "fccs_id": "2",
                        "pct": 60,
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": {"CO": [12.0]},
                                    "smoldering": {"CO": [13.0]},
                                    "total": {"CO": [14.0]}
                                },
                                "blah": {
                                    "flaming": {"CO": [15.0]}
                                }
                            },
                            "bar": {
                                "baz": {
                                    "flaming": {"CO": [15.0]}
                                }
                            }
                        }
                    }
                ]
            })
        ]
        expected_summary = {
            "canopy": {
                "ladder fuels": {
                    "residual": {"CO": [13.0]},
                    "smoldering": {"CO": [15.0]},
                    "total": {"CO": [17.0]}
                },
                "midstory": {
                    "flaming": {"CO": [4.0]},
                    "residual": {"CO2": [4.0]}
                },
                "blah": {
                    "flaming": {"CO": [15.0]}
                }
            },
            "foo": {
                "bar": {
                    "baz": {"CO": [5.0]}
                }
            },
            "bar": {
                "baz": {
                    "flaming": {"CO": [15.0]}
                }
            }
        }
        summary = emissions.summarize(fires)
        assert summary == expected_summary

    def test_two_fires(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": {"CO": [1.0]},
                                    "smoldering": {"CO": [2.0]},
                                    "total": {"CO": [3.0]}
                                },
                                "midstory": {
                                    "flaming": {"CO": [4.0]},
                                    "residual": {"CO2": [4.0]}
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": {"CO": [5.0]}
                                }
                            }
                        }
                    },
                    {
                        "fccs_id": "2",
                        "pct": 60,
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": {"CO": [12.0]},
                                    "smoldering": {"CO": [13.0]},
                                    "total": {"CO": [14.0]}
                                },
                                "blah": {
                                    "flaming": {"CO": [15.0]}
                                }
                            },
                            "bar": {
                                "baz": {
                                    "flaming": {"CO": [15.0]}
                                }
                            }
                        }
                    }
                ]
            }),
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "3",
                        "pct": 60,
                        "emissions": {
                            "bar": {
                                "baz": {
                                    "flaming": {"CO": [25.0]}
                                },
                                "baaaaz": {
                                    "redisual": {"CO": [32.0]}
                                }
                            },
                            "fooooo": {
                                "baz": {
                                    "flaming": {"CO": [113.0]}
                                }
                            }
                        }
                    }
                ]
            })
        ]
        expected_summary = {
            "canopy": {
                "ladder fuels": {
                    "residual": {"CO": [13.0]},
                    "smoldering": {"CO": [15.0]},
                    "total": {"CO": [17.0]}
                },
                "midstory": {
                    "flaming": {"CO": [4.0]},
                    "residual": {"CO2": [4.0]}
                },
                "blah": {
                    "flaming": {"CO": [15.0]}
                }
            },
            "foo": {
                "bar": {
                    "baz": {"CO": [5.0]}
                }
            },
            "bar": {
                "baz": {
                    "flaming": {"CO": [40.0]}
                },
                "baaaaz": {
                    "redisual": {"CO": [32.0]}
                }
            },
            "fooooo": {
                "baz": {
                    "flaming": {"CO": [113.0]}
                }
            }
        }
        summary = emissions.summarize(fires)
        assert summary == expected_summary

