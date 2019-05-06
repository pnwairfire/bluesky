"""Unit tests for bluesky.datetimeutils"""

__author__ = "Joel Dubowy"


from py.test import raises

from bluesky import datautils
from bluesky.models import activity
from bluesky.models.fires import Fire

# TODO: moke Fire class

class MockFiresManager(object):
    def __init__(self, fires):
        self.fires = [Fire(f) for f in fires]

    @property
    def fire_failure_handler(self):
        class klass(object):
            def __init__(self, fire):
                pass

            def __enter__(self):
                pass

            def __exit__(self, e_type, value, tb):
                pass

        return klass

    def summarize(self, **summary):
        self.summary = summary


class TestSummarizeAllLevels(object):

    def test_no_fires(self):
        fm = MockFiresManager([])
        datautils.summarize_all_levels(fm, 'emissions')
        assert fm.fires == []
        assert fm.summary == {"emissions": {'summary': {'total': 0.0}}}

    def test_no_active_areas(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750"
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        assert fm.fires == [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "emissions": {'summary': {'total': 0.0}}
        }]
        assert fm.summary == {"emissions": {'summary': {'total': 0.0}}}

    def test_empty_active_areas(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity_areas": []
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        assert fm.fires == [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "activity_areas": [],
            "emissions": {'summary': {'total': 0.0}}
        }]
        assert fm.summary == {"emissions": {'summary': {'total': 0.0}}}

    def test_no_locations(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                    }]
                }]
            }
        ])
        with raises(ValueError) as e_info:
            datautils.summarize_all_levels(fm, 'emissions')
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG

    def test_no_fuelbeds(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {'area': 34, 'lat': 45.0, 'lng': -120.0}
                        ]
                    }]
                }]
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        assert fm.fires == [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "activity": [{
                "active_areas": [{
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {'area': 34, 'lat': 45.0, 'lng': -120.0}
                    ],
                    "emissions": {'summary': {'total': 0.0}}
                }],
                "emissions": {'summary': {'total': 0.0}}
            }],
            "emissions": {'summary': {'total': 0.0}}
        }]
        assert fm.summary == {"emissions": {'summary': {'total': 0.0}}}

    def test_one_fire_one_fuelbed_no_emissions(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds": {}
                            }
                        ]
                    }]
                }]
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        assert fm.fires == [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "activity": [{
                "active_areas": [{
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {
                            'area': 34, 'lat': 45.0, 'lng': -120.0,
                            "fuelbeds": {}
                        }
                    ],
                    "emissions": {'summary': {'total': 0.0}}
                }],
                "emissions": {'summary': {'total': 0.0}}
            }],
            "emissions": {'summary': {'total': 0.0}}
        }]
        assert fm.summary == {"emissions": {'summary': {'total': 0.0}}}

    def test_one_fire_one_fuelbed_with_emissions(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds":  [{
                                    "emissions": {
                                        "flaming": {"PM2.5": [10]},
                                        "smoldering":{"PM2.5": [7]},
                                        "total": {"PM2.5": [22]} # incorrect, but should be ignored
                                    }
                                }]
                            }
                        ]
                    }]
                }]
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        expected_fires = [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "activity": [{
                "active_areas": [{
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {
                            'area': 34, 'lat': 45.0, 'lng': -120.0,
                            "fuelbeds": [{
                                "emissions": {
                                    "flaming": {"PM2.5": [10]},
                                    "smoldering":{"PM2.5": [7]},
                                    "total": {"PM2.5": [22]} # incorrect, but should be ignored
                                }
                            }]
                        }
                    ],
                    "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
                }],
                "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
            }],
            "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
        }]
        assert fm.fires == expected_fires
        assert fm.summary == {
            "emissions": {
                "flaming": {"PM2.5": [10]},
                "smoldering": {"PM2.5": [7]},
                'summary': {'PM2.5': 17.0, 'total': 17.0}
            }
        }

    def test_one_fire_one_location_two_fuelbed(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds":  [
                                    {
                                        "emissions": {
                                            "flaming": {"PM2.5": [10]},
                                            "smoldering":{"PM2.5": [7]},
                                            "total": {"PM2.5": [22]}, # incorrect, but should be ignored
                                        }
                                    },
                                    {
                                        "emissions": {
                                            "flaming": {"PM2.5": [42]},
                                            "residual":{"PM2.5": [1],"CO": [123]},
                                            "total": {"PM2.5": [22]}, # incorrect, but should be ignored
                                        }

                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        expected_fires = [{
            "id": "SF11C14225236095807750",
            'fuel_type': 'natural',
            'type': 'wildfire',
            "activity": [{
                "active_areas": [{
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {
                            'area': 34, 'lat': 45.0, 'lng': -120.0,
                            "fuelbeds": [
                                {
                                    "emissions": {
                                        "flaming": {
                                            "PM2.5": [10]
                                        },
                                        "smoldering":{
                                            "PM2.5": [7]
                                        },
                                        "total": {
                                            "PM2.5": [22] # incorrect, but should be ignored
                                        },
                                    }
                                },
                                {
                                    "emissions": {
                                        "flaming": {
                                            "PM2.5": [42]
                                        },
                                        "residual":{
                                            "PM2.5": [1],
                                            "CO": [123]
                                        },
                                        "total": {
                                            "PM2.5": [22] # incorrect, but should be ignored
                                        },
                                    }

                                }
                            ]
                        }
                    ],
                    "emissions": {'summary': {'PM2.5': 60.0, 'CO': 123.0, 'total': 183.0}}
                }],
                "emissions": {'summary': {'PM2.5': 60.0, 'CO': 123.0, 'total': 183.0}}
            }],
            "emissions": {'summary': {'PM2.5': 60.0, 'CO': 123.0, 'total': 183.0}}
        }]
        assert fm.fires == expected_fires
        expected_summary = {
            "emissions": {
                "flaming": {"PM2.5": [52.0]},
                "residual": {"PM2.5": [1.0], "CO": [123.0]},
                "smoldering": {"PM2.5": [7.0]},
                'summary': {'PM2.5': 60.0, "CO":123.0, 'total': 183.0}
            }
        }
        assert fm.summary == expected_summary

    def test_one_fire_one_ac_two_aa_two_locations_two_fuelbed(self):
        pass

    def test_one_fire_two_ac_two_aa_two_locations_two_fuelbed(self):
        pass

    def test_two_fires_two_ac_two_aa_two_locations_two_fuelbed(self):
        fm = MockFiresManager([
            {
                "id": "SF11C14225236095807750",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds":  [
                                    {
                                        "emissions": {
                                            "flaming": {"PM2.5": [10]},
                                            "smoldering":{"PM2.5": [7]},
                                            "total": {"PM2.5": [22]}, # incorrect, but should be ignored
                                        }
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            },
            {
                "id": "sfkjfsdlksdflkjdf",
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds":  [
                                    {
                                        "emissions": {
                                            "flaming": {"PM2.5": [42]},
                                            "residual":{"PM2.5": [1],"CO": [123]},
                                            "total": {"PM2.5": [22]}, # incorrect, but should be ignored
                                        }

                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        ])
        datautils.summarize_all_levels(fm, 'emissions')
        expected_fires = [
            {
                "id": "SF11C14225236095807750",
                'fuel_type': 'natural',
                'type': 'wildfire',
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds": [
                                    {
                                        "emissions": {
                                            "flaming": {
                                                "PM2.5": [10]
                                            },
                                            "smoldering":{
                                                "PM2.5": [7]
                                            },
                                            "total": {
                                                "PM2.5": [22] # incorrect, but should be ignored
                                            },
                                        }
                                    }
                                ]
                            }
                        ],
                        "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
                    }],
                    "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
                }],
                "emissions": {'summary': {'PM2.5': 17.0, 'total': 17.0}}
            },
            {
                "id": "sfkjfsdlksdflkjdf",
                'fuel_type': 'natural',
                'type': 'wildfire',
                "activity": [{
                    "active_areas": [{
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {
                                'area': 34, 'lat': 45.0, 'lng': -120.0,
                                "fuelbeds":  [
                                    {
                                        "emissions": {
                                            "flaming": {
                                                "PM2.5": [42]
                                            },
                                            "residual":{
                                                "PM2.5": [1],
                                                "CO": [123]
                                            },
                                            "total": {
                                                "PM2.5": [22] # incorrect, but should be ignored
                                            },
                                        }
                                    }
                                ]
                            }
                        ],
                        "emissions": {'summary': {'PM2.5': 43.0, 'CO': 123.0, 'total': 166.0}}
                    }],
                    "emissions": {'summary': {'PM2.5': 43.0, 'CO': 123.0, 'total': 166.0}}
                }],
                "emissions": {'summary': {'PM2.5': 43.0, 'CO': 123.0, 'total': 166.0}}
            }
        ]
        assert fm.fires == expected_fires
        expected_summary = {
            "emissions": {
                "flaming": {"PM2.5": [52.0]},
                "residual": {"PM2.5": [1.0], "CO": [123.0]},
                "smoldering": {"PM2.5": [7.0]},
                'summary': {'PM2.5': 60.0, "CO":123.0, 'total': 183.0}
            }
        }
        assert fm.summary == expected_summary

    def test_multi(self):
        pass
