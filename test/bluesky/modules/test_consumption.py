"""Unit tests for bluesky.modules.consumption"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import copy

from py.test import raises

from bluesky.models.fires import Fire
from bluesky.modules import consumption

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
        assert consumption.summarize([]) == {}

    def test_one_fire_one_fuelbed(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": [1.0],
                                    "smoldering": [2.0],
                                    "total": [3.0]
                                },
                                "midstory": {
                                    "flaming": [4.0]
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": [5.0]
                                }
                            }
                        }
                    }
                ]
            })
        ]
        assert consumption.summarize(fires) == fires[0]['fuelbeds'][0]['consumption']

    def test_one_fire_two_fuelbeds(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": [1.0],
                                    "smoldering": [2.0],
                                    "total": [3.0]
                                },
                                "midstory": {
                                    "flaming": [4.0]
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": [5.0]
                                }
                            }
                        }
                    },
                    {
                        "fccs_id": "2",
                        "pct": 60,
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": [12.0],
                                    "smoldering": [13.0],
                                    "total": [14.0]
                                },
                                "blah": {
                                    "flaming": [15.0]
                                }
                            },
                            "bar": {
                                "baz": {
                                    "flaming": [15.0]
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
                    "residual": [13.0],
                    "smoldering": [15.0],
                    "total": [17.0]
                },
                "midstory": {
                    "flaming": [4.0]
                },
                "blah": {
                    "flaming": [15.0]
                }
            },
            "foo": {
                "bar": {
                    "baz": [5.0]
                }
            },
            "bar": {
                "baz": {
                    "flaming": [15.0]
                }
            }
        }
        summary = consumption.summarize(fires)
        assert summary == expected_summary

    def test_two_fires(self):
        fires = [
            Fire({
                "location":{"area": 10},
                "fuelbeds":[
                    {
                        "fccs_id": "1",
                        "pct": 40,
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": [1.0],
                                    "smoldering": [2.0],
                                    "total": [3.0]
                                },
                                "midstory": {
                                    "flaming": [4.0]
                                }
                            },
                            "foo": {
                                "bar": {
                                    "baz": [5.0]
                                }
                            }
                        }
                    },
                    {
                        "fccs_id": "2",
                        "pct": 60,
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "residual": [12.0],
                                    "smoldering": [13.0],
                                    "total": [14.0]
                                },
                                "blah": {
                                    "flaming": [15.0]
                                }
                            },
                            "bar": {
                                "baz": {
                                    "flaming": [15.0]
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
                        "consumption": {
                            "bar": {
                                "baz": {
                                    "flaming": [25.0]
                                },
                                "baaaaz": {
                                    "redisual": [32.0]
                                }
                            },
                            "fooooo": {
                                "baz": {
                                    "flaming": [113.0]
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
                    "residual": [13.0],
                    "smoldering": [15.0],
                    "total": [17.0]
                },
                "midstory": {
                    "flaming": [4.0]
                },
                "blah": {
                    "flaming": [15.0]
                }
            },
            "foo": {
                "bar": {
                    "baz": [5.0]
                }
            },
            "bar": {
                "baz": {
                    "flaming": [40.0]
                },
                "baaaaz": {
                    "redisual": [32.0]
                }
            },
            "fooooo": {
                "baz": {
                    "flaming": [113.0]
                }
            }
        }
        summary = consumption.summarize(fires)
        assert summary == expected_summary

