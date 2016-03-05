"""Unit tests for bluesky.datautils"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import copy
import datetime
from py.test import raises

import numpy

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
        e = {"summary": {"total": 0.0}}
        assert datautils.summarize([], 'consumption') == e
        assert datautils.summarize([], 'consumption', include_details=False) == e

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
        expected = copy.deepcopy(fires[0]['fuelbeds'][0]['consumption'])
        expected['canopy']['ladder fuels'].pop("total")
        expected['summary'] = {
            "residual": 1.0,
            "smoldering": 2.0,
            "flaming": 4.0,
            "baz": 5.0,
            "total": 12
        }
        assert datautils.summarize(fires, 'consumption') == expected
        assert datautils.summarize(fires, 'consumption', include_details=False) == {
            "summary": expected["summary"]
        }

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
                    "smoldering": [15.0]
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
            },
            "summary": {
                "residual": 13.0,
                "smoldering": 15.0,
                "flaming": 34.0,
                "baz": 5.0,
                "total": 67.0
            }
        }
        summary = datautils.summarize(fires, 'consumption')
        assert summary == expected_summary
        assert datautils.summarize(fires, 'consumption', include_details=False) == {
            "summary": expected_summary["summary"]
        }

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
                        },
                        "summary": {
                            "sdf": {
                                "sdf":[23.0]
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
                    "smoldering": [15.0]
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
            },
            "summary": {
                "residual": 13.0,
                "redisual": 32.0,
                "smoldering": 15.0,
                "flaming": 172.0,
                "baz": 5.0,
                "total": 237.0

            }
        }
        summary = datautils.summarize(fires, 'consumption')
        assert summary == expected_summary
        assert datautils.summarize(fires, 'consumption', include_details=False) == {
            "summary": expected_summary["summary"]
        }

class TestSummarizeEmissions(object):

    def test_no_fires(self):
        e = {"summary": {"total": 0.0}}
        assert datautils.summarize([], 'emissions') == e
        assert datautils.summarize([], 'emissions', include_details=False) == e

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
        expected = copy.deepcopy(fires[0]['fuelbeds'][0]['emissions'])
        expected['canopy']['ladder fuels'].pop("total")
        expected['summary'] = {
            "CO": 12.0,
            "CO2": 4.0,
            "total": 16.0
        }
        actual = datautils.summarize(fires, 'emissions')
        assert actual == expected
        assert datautils.summarize(fires, 'emissions', include_details=False) == {
            "summary": expected["summary"]
        }

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
                    "smoldering": {"CO": [15.0]}
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
            },
            "summary":{
                "CO": 67.0,
                "CO2": 4.0,
                "total": 71.0
            }
        }
        summary = datautils.summarize(fires, 'emissions')
        assert summary == expected_summary
        assert datautils.summarize(fires, 'emissions', include_details=False) == {
            "summary": expected_summary["summary"]
        }

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
            },
            "summary":{
                "CO": 237.0,
                "CO2": 4.0,
                "total": 241.0
            }
        }
        summary = datautils.summarize(fires, 'emissions')
        assert summary == expected_summary
        assert datautils.summarize(fires, 'emissions', include_details=False) == {
            "summary": expected_summary["summary"]
        }

class TestMultiplyNestedData(object):

    def test_scalar(self):
        with raises(ValueError) as e:
            datautils.multiply_nested_data(1, 2)

    def test_list(self):
        d = [1, 1.5, 'sdf']
        e = [2, 3, 'sdf']
        datautils.multiply_nested_data(d, 2)

    def test_ndarray(self):
        # Note: if you include 'sdf' in d, as in test_array, all
        # values in d become cast to numpy.string_
        d = numpy.array([1, 1.5])
        e = numpy.array([2, 3])
        datautils.multiply_nested_data(d, 2)
        for i in range(len(d)):
            assert d[i] == e[i]

    def test_dict(self):
        d = dict(a=1, b=1.5, c='sdf')
        e = dict(a=2, b=3, c='sdf')
        datautils.multiply_nested_data(d, 2)
        assert d == e

    def test_multi(self):
        d = {
            "a": 1,
            "b": [1.5, 5],
            "c": 'sdf',
            "d": {
                "e": '234',
                "f": 3.4
            }
        }
        e = {
            "a": 2,
            "b": [3, 10],
            "c": 'sdf',
            "d": {
                "e": '234',
                "f": 6.8
            }
        }
        datautils.multiply_nested_data(d, 2)
        assert d == e

class TestSumNestedData(object):

    def test_string(self):
        with raises(ValueError) as e_info:
            datautils.sum_nested_data("sdf")

    def test_scalar(self):
        with raises(ValueError) as e_info:
            datautils.sum_nested_data(1)

    def test_array(self):
        with raises(ValueError) as e_info:
            datautils.sum_nested_data([1,2])

    def test_dict_strings(self):
        with raises(ValueError) as e_info:
            datautils.sum_nested_data({'a': 'sdf','b':2})

    def test_empty_dict(self):
        assert {} == datautils.sum_nested_data({})

    def test_flat_dict_scalars(self):
        d = {'a': 12, 'b': 33}
        assert d == datautils.sum_nested_data(d)

    def test_flat_dict_arrays(self):
        d = {'a': [2], 'b': [1, 2, 3]}
        e = {'a': 2, 'b': 6}
        assert e == datautils.sum_nested_data(d)

    def test_nested_dict_scalars(self):
        d = {
            'foo': {'a': 12, 'b': 6},
            'bar': {'a': 23, 'c': 4}
        }
        e = {'a': 35, 'b': 6, 'c': 4}
        assert e == datautils.sum_nested_data(d)

    def test_nested_dict_arrays(self):
        d = {
            'foo': {'a': [2, 3], 'b': [2, 2]},
            'bar': {'a':[3], 'c': [3,2,1]}
        }
        e = {'a': 8, 'b': 4, 'c': 6}
        assert e == datautils.sum_nested_data(d)

    def test_nested_dict_scalars_and_arrays(self):
        d = {
            'foo': {'a': [2, 3], 'b': 3},
            'bar': {'a':6, 'c': [3,2,1]}
        }
        e = {'a': 11, 'b': 3, 'c': 6}
        assert e == datautils.sum_nested_data(d)

    def test_array_of_nested_dicts_with_scalars_and_arrays(self):
        d = {
            'foo': {'a': [2, 3], 'b': 3},
            'bar': {'a':6, 'c': [3, 2, 1]}
        }
        d2 = {
            'a': 2, 'sdfsdf':[2, 5]
        }
        e = {'a': 13, 'b': 3, 'c': 6, 'sdfsdf': 7}
        assert e == datautils.sum_nested_data([d, d2])

    def test_nested_dict_scalars_and_arrays_with_skip_keys(self):
        d = {
            'foo': {'a': [2, 3], 'b': 3},
            'bar': {'a':6, 'c': [3,2,1]},
            'baz': {'a': 2, 'b': [3,2,4], 'c': 44}
        }
        e = {'b': 9, 'c': 50}
        assert e == datautils.sum_nested_data(d, 'foo', 'a')

class TestFormatDatetimes(object):

    def test_scalar(self):
        assert 'sdf' == datautils.format_datetimes('sdf')
        assert 1 == datautils.format_datetimes(1)
        assert '2015-01-02T03:02:01' == datautils.format_datetimes(
            datetime.datetime(2015, 1,2,3,2,1))

    def test_list(self):
        d = ['sdf', 1, datetime.datetime(2015, 1,2,3,2,1)]
        e = ['sdf', 1, '2015-01-02T03:02:01']
        # formated data is returned...
        assert e == datautils.format_datetimes(d)
        # ...and modified inplace as well
        assert e == d

    def test_dict(self):
        d = {
            'a': 'sdf',
            datetime.datetime(2015,2,2,3,2,1): 1,
            'c': datetime.datetime(2015,1,2,3,2,1)
        }
        e = {
            'a': 'sdf',
            '2015-02-02T03:02:01': 1,
            'c': '2015-01-02T03:02:01'
        }

        # formated data is returned...
        assert e == datautils.format_datetimes(d)
        # ...and modified inplace as well
        assert e == d

    def test_multi(self):
        d = {
            "a": 1,
            "b": [1.5, datetime.datetime(2015, 1,2,3,2,1)],
            datetime.datetime(2015, 3,2,3,2,1): 'sdf',
            "d": {
                "e": '234',
                "f": datetime.datetime(2015, 2,2,3,2,1)
            }
        }
        e = {
            "a": 1,
            "b": [1.5, '2015-01-02T03:02:01'],
            '2015-03-02T03:02:01': 'sdf',
            "d": {
                "e": '234',
                "f": '2015-02-02T03:02:01'
            }
        }
        # formated data is returned...
        assert e == datautils.format_datetimes(d)
        # ...and modified inplace as well
        assert e == d
