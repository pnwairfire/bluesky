"""Unit tests for bluesky.datautils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

#from py.test import raises

from bluesky import datautils
from bluesky.models.fires import Fire

##
## Tests for deepmerge
##

class TestDeepMerge(object):

    def test_both_empty(self):
        a = {}
        b = {}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {}

    def test_one_of_two_empty(self):
        a = {'a':1}
        b = {}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1}

        a = {}
        b = {'a':1}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1}

    def test_non_nested(self):
        a = {'a':1, 'b':34}
        b = {'b':23, 'c':34343}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1,'b':23, 'c':34343}

    def test_nested(self):
        a = {'a':{'a':1,'b':2},'c':2}
        b = {'a':{'s':1,'b':6},'b':9}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':{'a':1,'b':6, 's':1},'c':2,'b':9}

##
## Tests for summarize
##

class TestSummarizeConsumption(object):

    def test_no_fires(self):
        assert datautils.summarize([], 'consumption') == {}

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
        assert datautils.summarize(fires, 'consumption') == fires[0]['fuelbeds'][0]['consumption']

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
        summary = datautils.summarize(fires, 'consumption')
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
        summary = datautils.summarize(fires, 'consumption')
        assert summary == expected_summary

class TestSummarizeEmissions(object):

    def test_no_fires(self):
        assert datautils.summarize([], 'emissions') == {}

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
        assert datautils.summarize(fires, 'emissions') == fires[0]['fuelbeds'][0]['emissions']

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
        summary = datautils.summarize(fires, 'emissions')
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
        summary = datautils.summarize(fires, 'emissions')
        assert summary == expected_summary
