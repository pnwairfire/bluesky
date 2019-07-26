"""Unit tests for bluesky.filtermerge.filter"""

__author__ = "Joel Dubowy"

import datetime

from py.test import raises

from bluesky.config import Config
from bluesky.filtermerge.filter import FireActivityFilter
from bluesky.models import fires

## TODO: unit test fires.FiresMerger directly,
##    using mock FireManager object


class TestFiresManagerFilterFiresNoneSpecified(object):

    ## Filtering

    def setup(self):
        self.fm = fires.FiresManager()
        self.init_fires = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
        ]
        self.fm.fires = self.init_fires

    def test_no_filters_specified(self, reset_config):
        ## No filters specifeid
        Config.set(False, 'filter', 'skip_failures')
        with raises(fires.FireActivityFilter.FilterError) as e_info:
            self.fm.filter_fires()
        assert self.fm.num_fires == 1
        assert e_info.value.args[0] == fires.FireActivityFilter.NO_FILTERS_MSG
        Config.set(True, 'filter', 'skip_failures')
        self.fm.filter_fires()
        assert self.fm.num_fires == 1
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))


class TestFiresManagerFilterFiresByCountry(object):

    def setup(self):
        self.fm = fires.FiresManager()
        self.init_fires = [
            fires.Fire({'id': '01', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '02', 'name': 'n2', 'bar':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '03', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "ZZ"}, {'country': "ZZ"}]}]}),
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '05', 'name': 'n5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "USA"}]}]}),
            fires.Fire({'id': '06', 'name': 'n6', 'bar1': 1 , 'baz':'baz1',
                "activity": [{"active_areas": [{'country': ''}]}]}),
            fires.Fire({'id': '07', 'name': 'n7', 'bar2':'a2', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '08', 'name': 'n8', 'bar2':'adfsdf', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '09', 'name': 'n9', 'bar2': 2 , 'baz':'baz2',
                "activity": [{"active_areas": [{'country': 'Unknown'}]}]}),
            fires.Fire({'id': '10', 'name': 'n10', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "USA"}]}]}),
            fires.Fire({'id': '11', 'name': 'n11', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "BZ"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "ZZ"}]}, {"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '13', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "ZZ"}]}, {"active_areas": [{'country': "ZZ"}]}]}),
            # 14 is same as 12 exept the two active area objects are with the same activity object
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "ZZ"}, {'country': "UK"}]}]})
        ]
        self.fm.fires = self.init_fires
        assert self.fm.num_fires == 14


    def test_empty_config(self, reset_config):
        Config.set({}, 'filter', 'country')
        Config.set(False, 'filter', 'skip_failures')
        with raises(fires.FireActivityFilter.FilterError) as e_info:
            self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert e_info.value.args[0] == fires.FireActivityFilter.MISSING_FILTER_CONFIG_MSG
        Config.set(True, 'filter', 'skip_failures')
        self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_neither_whitelist_or_blacklist_is_specified(self, reset_config):
        Config.set({'foo': 'bar'}, 'filter', 'country')
        Config.set(False, 'filter', 'skip_failures')
        with raises(fires.FireActivityFilter.FilterError) as e_info:
            self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert e_info.value.args[0] == fires.FireActivityFilter.SPECIFY_WHITELIST_OR_BLACKLIST_MSG
        Config.set(True, 'filter', 'skip_failures')
        self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_both_whitelist_or_blacklist_are_specified(self, reset_config):
        Config.set(False, 'filter', 'skip_failures')
        Config.set(["ZZ"], 'filter', 'country', 'blacklist')
        Config.set(["YY"], 'filter', 'country', 'whitelist')
        with raises(fires.FireActivityFilter.FilterError) as e_info:
            self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert e_info.value.args[0] == fires.FireActivityFilter.SPECIFY_WHITELIST_OR_BLACKLIST_MSG
        Config.set(True, 'filter', 'skip_failures')
        self.fm.filter_fires()
        assert self.fm.num_fires == 14
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

        Config.set(False, 'filter', 'skip_failures')
        Config.set(["ZZ"], 'filter', 'country', 'blacklist')
        Config.set(None, 'filter', 'country', 'whitelist')
        self.fm.filter_fires()
        expected = [
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '05', 'name': 'n5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "USA"}]}]}),
            fires.Fire({'id': '06', 'name': 'n6', 'bar1': 1 , 'baz':'baz1',
                "activity": [{"active_areas": [{'country': ''}]}]}),
            fires.Fire({'id': '07', 'name': 'n7', 'bar2':'a2', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '08', 'name': 'n8', 'bar2':'adfsdf', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '09', 'name': 'n9', 'bar2': 2 , 'baz':'baz2',
                "activity": [{"active_areas": [{'country': 'Unknown'}]}]}),
            fires.Fire({'id': '10', 'name': 'n10', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "USA"}]}]}),
            fires.Fire({'id': '11', 'name': 'n11', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "BZ"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
        ]
        assert self.fm.num_fires == 10
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        Config.set(["USA", "CA", "UK", "BZ"],
            'filter', 'country', 'whitelist')
        Config.set(None, 'filter', 'country', 'blacklist')
        self.fm.filter_fires()
        expected = [
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '05', 'name': 'n5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "USA"}]}]}),
            fires.Fire({'id': '07', 'name': 'n7', 'bar2':'a2', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '08', 'name': 'n8', 'bar2':'adfsdf', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '10', 'name': 'n10', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "USA"}]}]}),
            fires.Fire({'id': '11', 'name': 'n11', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "BZ"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
        ]
        assert self.fm.num_fires == 8
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        Config.set(["USA"], 'filter', 'country', 'blacklist')
        Config.set(None, 'filter', 'country', 'whitelist')
        self.fm.filter_fires()
        expected = [
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '07', 'name': 'n7', 'bar2':'a2', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '08', 'name': 'n8', 'bar2':'adfsdf', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '11', 'name': 'n11', "barj": "jj", "baz": 99,
                "activity": [{"active_areas": [{"country": "BZ"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
        ]
        assert self.fm.num_fires == 6
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        Config.set(["USA", "CA", "UK"], 'filter', 'country', 'whitelist')
        Config.set(None, 'filter', 'country', 'blacklist')
        self.fm.filter_fires()
        expected = [
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '07', 'name': 'n7', 'bar2':'a2', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '08', 'name': 'n8', 'bar2':'adfsdf', 'baz':'baz2',
                "activity": [{"active_areas": [{'country': "CA"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
        ]
        assert self.fm.num_fires == 5
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        Config.set(["USA", "CA"], 'filter', 'country', 'blacklist')
        Config.set(None, 'filter', 'country', 'whitelist')
        self.fm.filter_fires()
        expected = [
            fires.Fire({'id': '04', 'name': 'n4', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '12', 'name': 'n3', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
            fires.Fire({'id': '14', 'name': 'n3.5', 'bar1':'a1', 'baz':'baz1',
                "activity": [{"active_areas": [{'country': "UK"}]}]}),
        ]
        assert self.fm.num_fires == 3
        assert expected == self.fm.fires

        Config.set(["UK", "CA"], 'filter', 'country', 'blacklist')
        Config.set(None, 'filter', 'country', 'whitelist')
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == self.fm.fires

        # call again with no fires
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == self.fm.fires


class TestFiresManagerFilterFiresByLocation(object):

    def setup(self):
        self.fm = fires.FiresManager()
        self.init_fires = [
            fires.Fire({'id': '1', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -80.0}]}]}]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas': [{'specified_points':[{'lat': 45.0, 'lng': -81.0}, {'lat': 55.0, 'lng': -79.0}]}]}]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-61, 71], [-61, 69], [-59, 69], [-59, 71], [-61, 71]]}}]}]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas': [{'specified_points':[{'lat': 61.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-51,61], [-49, 61], [-49, 59], [-51, 59], [-51, 61]]}}]}]}),
            fires.Fire({'id': '8', 'activity': [{'active_areas': [{'specified_points':[{'lat': 70.0, 'lng': -120.0}]}]}]}),
            fires.Fire({'id': '9', 'activity': [{'active_areas': [{'specified_points':[{'lat': -10.0, 'lng': 10.0}]}]}]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas': [{'specified_points': [{'lat': -10.0, 'lng': -10.0}]}]},
                {'active_areas': [{'specified_points': [{'lat': 40.0, 'lng': -80.0}]}]}
            ]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas': [{'specified_points': [{'lat': -10.0, 'lng': 10.0}]}]},
                {'active_areas': [{'specified_points': [{'lat': -11.0, 'lng': 9.0}]}]},
            ]})
        ]
        self.fm.fires = self.init_fires
        assert self.fm.num_fires == 11

    def test_invalid_config(self, reset_config):
        ## Failure situations
        scenarios = (
            # empty config
            ({}, fires.FireActivityFilter.MISSING_FILTER_CONFIG_MSG),
            # boundary not specified
            ({'foo': 'bar'}, fires.FireActivityFilter.SPECIFY_BOUNDARY_MSG),

            ## Invalid boundary
            # Invalid and insufficient keys
            ({'boundary': {"foo": "bar"}},
                fires.FireActivityFilter.INVALID_BOUNDARY_FIELDS_MSG),
            # Invalid keys
            ({'boundary': {
                "sdfsdf": 123,
                "ne": {"lat": 88.12, "lng": 40},
                "sw": {"lat": -50.75,"lng": -131.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_FIELDS_MSG),
            # insufficient keys
            ({'boundary': {
                "ne": {"lng": 40},
                "sw": {"lat": -50.75,"lng": -131.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_FIELDS_MSG),
            ({'boundary': {
                "sw": {"lat": -50.75,"lng": -131.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_FIELDS_MSG),
            # lat/lng outside of valid range
            ({'boundary': {
                "ne": {"lat": 98.12, "lng": 40},
                "sw": {"lat": -50.75,"lng": -131.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_MSG),
            # sw east of ne
            ({'boundary': {
                "ne": {"lat": 68.12, "lng": 40},
                "sw": {"lat": 50.75,"lng": 50.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_MSG),
            # sw north of ne
            ({'boundary': {
                "ne": {"lat": 48.12, "lng": 40},
                "sw": {"lat": 50.75,"lng": -50.5}}},
                fires.FireActivityFilter.INVALID_BOUNDARY_MSG)
        )
        for config, err_msg in scenarios:
            Config.set(config, 'filter', 'location')
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 11
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))
            assert e_info.value.args[0] == err_msg
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 11
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))


    def test_invalid_fires(self, reset_config):
        Config.set({"ne": {"lat": 88.12, "lng": 40},
            "sw": {"lat": -50.75,"lng": -131.5}},
            'filter', 'location', 'boundary')
        scenarios = (
            # specified point missing lat
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{'specified_points':[{'lng': -80.0}]}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # specified point missing lng
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{'specified_points':[{'lat': 44.0}]}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # specified point missing both lat and lng
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{'specified_points': [{}]}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # perimeter missing polygon
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{'perimeter': {}}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # perimeter empty polygon
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{'perimeter': {'polygon':[]}}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
        )
        for f, err_msg in scenarios:
            self.fm.fires = [f]
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires
            assert e_info.value.args[0].index(err_msg) > 0
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires

    def test_noops(self, reset_config):
        ## noops
        Config.set({"ne": {"lat": 88.12, "lng": 40},
            "sw": {"lat": -50.75,"lng": -131.5}},
            'filter', 'location', 'boundary')
        self.fm.filter_fires()
        assert self.fm.num_fires == 11
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))


    def test_successful_filtering(self, reset_config):
        """
        TODO: split this method into separate test cases
        """
        # squeeze sw lat
        Config.set({"ne": {"lat": 88.12, "lng": 40},
            "sw": {"lat": -5.75,"lng": -131.5}},
            'filter', 'location', 'boundary')
        expected = [
            fires.Fire({'id': '1', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -80.0}]}]}]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas': [{'specified_points':[{'lat': 45.0, 'lng': -81.0}, {'lat': 55.0, 'lng': -79.0}]}]}]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-61, 71], [-61, 69], [-59, 69], [-59, 71], [-61, 71]]}}]}]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas': [{'specified_points':[{'lat': 61.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-51,61], [-49, 61], [-49, 59], [-51, 59], [-51, 61]]}}]}]}),
            fires.Fire({'id': '8', 'activity': [{'active_areas': [{'specified_points':[{'lat': 70.0, 'lng': -120.0}]}]}]}),
            fires.Fire({'id': '10', 'activity': [{'active_areas': [{'specified_points': [{'lat': 40.0, 'lng': -80.0}]}]}]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 9
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # squeeze sw lng
        Config.set({"ne": {"lat": 88.12, "lng": 40},
            "sw": {"lat": -5.75,"lng": -110.5}},
            'filter', 'location', 'boundary')
        expected = [
            fires.Fire({'id': '1', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -80.0}]}]}]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas': [{'specified_points':[{'lat': 45.0, 'lng': -81.0}, {'lat': 55.0, 'lng': -79.0}]}]}]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-61, 71], [-61, 69], [-59, 69], [-59, 71], [-61, 71]]}}]}]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas': [{'specified_points':[{'lat': 61.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-51,61], [-49, 61], [-49, 59], [-51, 59], [-51, 61]]}}]}]}),
            fires.Fire({'id': '10', 'activity': [{'active_areas': [{'specified_points': [{'lat': 40.0, 'lng': -80.0}]}]}]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 8
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # squeeze ne lat
        Config.set({"ne": {"lat": 66.12, "lng": 40},
            "sw": {"lat": -5.75,"lng": -110.5}},
            'filter', 'location', 'boundary')
        expected = [
            fires.Fire({'id': '1', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -80.0}]}]}]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas': [{'specified_points':[{'lat': 45.0, 'lng': -81.0}, {'lat': 55.0, 'lng': -79.0}]}]}]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas': [{'specified_points':[{'lat': 61.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas': [{'perimeter': {'polygon': [[-51,61], [-49, 61], [-49, 59], [-51, 59], [-51, 61]]}}]}]}),
            fires.Fire({'id': '10', 'activity': [{'active_areas': [{'specified_points': [{'lat': 40.0, 'lng': -80.0}]}]}]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 7
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # squeeze ne lng
        Config.set({"ne": {"lat": 66.12, "lng": -55},
            "sw": {"lat": -5.75,"lng": -110.5}},
            'filter', 'location', 'boundary')
        expected = [
            fires.Fire({'id': '1', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -80.0}]}]}]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas': [{'specified_points':[{'lat': 45.0, 'lng': -81.0}, {'lat': 55.0, 'lng': -79.0}]}]}]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas': [{'specified_points':[{'lat': 40.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas': [{'specified_points':[{'lat': 61.0, 'lng': -60.0}]}]}]}),
            fires.Fire({'id': '10', 'activity': [{'active_areas': [{'specified_points': [{'lat': 40.0, 'lng': -80.0}]}]}]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 6
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # squeeze ne lng
        Config.set({"ne": {"lat": 63.12, "lng": -61},
            "sw": {"lat": 58.75,"lng": -62}},
            'filter', 'location', 'boundary')
        expected = [
            fires.Fire({'id': '3', 'activity': [{'active_areas': [{'specified_points':[{'lat': 60.0, 'lng': -62.0}]}]}]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 1
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # squeeze out last fire
        Config.set({"ne": {"lat": 63.12, "lng": -61},
            "sw": {"lat": 60.75,"lng": -62}},
            'filter', 'location', 'boundary')
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == sorted(self.fm.fires, key=lambda e: int(e.id))

        # call again with no fires
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == sorted(self.fm.fires, key=lambda e: int(e.id))


class TestFiresManagerFilterFiresByArea(object):

    def setup(self):
        self.fm = fires.FiresManager()
        self.init_fires = [
            fires.Fire({'id': '1', 'activity': [{'active_areas':[{'specified_points': [{'area': 45}]}]} ]}),
            fires.Fire({'id': '2', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}, {'area': 40}]}]} ]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}]}]} ]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas':[{'perimeter': {'area': 65}}]} ]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas':[{'specified_points': [{'area': 85}]}]} ]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas':[{'specified_points': [{'area': 75}], 'perimeter': {'area': 90}}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas':[{'specified_points': [{'area': 50}]}]} ]}),
            fires.Fire({'id': '8', 'activity': [{'active_areas':[{'specified_points': [{'area': 30}]}]} ]}),
            fires.Fire({'id': '9', 'activity': [
                {'active_areas':[{'specified_points': [{'area': 45}]}]},
                {'active_areas':[{'specified_points': [{'area': 40}]}]}
            ]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas':[{'specified_points': [{'area': 45}]}]},
                {'active_areas':[{'perimeter': {'area': 65}}]}
            ]}),
            fires.Fire({'id': '11', 'activity': [{'active_areas':[{'specified_points': [{'area': 15}, {'area': 20}]}]} ]})
        ]
        self.fm.fires = self.init_fires
        assert self.fm.num_fires == 11

    def test_invalid_config(self, reset_config):
        scenarios = (
            # empty config
            ({}, fires.FireActivityFilter.MISSING_FILTER_CONFIG_MSG),
            # either min nor max is specified
            ({'foo': 'bar'}, fires.FireActivityFilter.SPECIFY_MIN_OR_MAX_MSG),

            ## Invalid min/max
            # both negative
            ({'min': -20, 'max': -2},
                fires.FireActivityFilter.INVALID_MIN_MAX_MUST_BE_POS_MSG),
            # min is negative
            ({'min': -20, 'max': 2},
                fires.FireActivityFilter.INVALID_MIN_MAX_MUST_BE_POS_MSG),
            ({'min': -20},
                fires.FireActivityFilter.INVALID_MIN_MAX_MUST_BE_POS_MSG),
            # max is negative
            ({'min': 20, 'max': -2},
                fires.FireActivityFilter.INVALID_MIN_MAX_MUST_BE_POS_MSG),
            ({'max': -2},
                fires.FireActivityFilter.INVALID_MIN_MAX_MUST_BE_POS_MSG),
            # min > max
            ({'min': 20, 'max': 2},
                fires.FireActivityFilter.INVALID_MIN_MUST_BE_LTE_MAX_MSG),
        )
        for config, err_msg in scenarios:
            Config.set(config, 'filter', 'area')
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 11
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))
            assert e_info.value.args[0] == err_msg
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 11
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_invalid_fire(self, reset_config):
        ## Invalid fire
        Config.set({'min': 0.0, 'max': 100.0}, 'filter', 'area')
        scenarios = (
            # missing area
            (fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{}]} ]} ]}),
             fires.FireActivityFilter.MISSING_ACTIVITY_AREA_MSG),
            (fires.Fire({'id': '3', 'activity': [{'active_areas':[
                {'specified_points': [{'area': 23}, {}]} ]} ]}), # second point missing area
             fires.FireActivityFilter.MISSING_ACTIVITY_AREA_MSG),
            (fires.Fire({'id': '3', 'activity': [{'active_areas':[{'perimeter': {} }]} ]}),
             fires.FireActivityFilter.MISSING_ACTIVITY_AREA_MSG),
            # negative area
            (fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{'area': -123}]} ]} ]}),
             fires.FireActivityFilter.NEGATIVE_ACTIVITY_AREA_MSG),
        )
        for f, err_msg in scenarios:
            self.fm.fires = [f]
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires
            assert e_info.value.args[0].index(err_msg) > 0
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires

    def test_noops(self, reset_config):
        ## noops
        Config.set(False, 'filter', 'skip_failures')
        # min only
        Config.set({'min': 20}, 'filter', 'area')
        self.fm.filter_fires()
        assert self.fm.num_fires == 11
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))
        # max only
        Config.set({'max': 120}, 'filter', 'area')
        self.fm.filter_fires()
        assert self.fm.num_fires == 11
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))
        # both min and max
        Config.set({'min': 20, 'max': 120}, 'filter', 'area')
        self.fm.filter_fires()
        assert self.fm.num_fires == 11
        assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_successful_filter_min(self):
        Config.set({'min': 47}, 'filter', 'area')
        expected = [
            fires.Fire({'id': '2', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}, {'area': 40}]}]} ]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}]}]} ]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas':[{'perimeter': {'area': 65}}]} ]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas':[{'specified_points': [{'area': 85}]}]} ]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas':[{'specified_points': [{'area': 75}], 'perimeter': {'area': 90}}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas':[{'specified_points': [{'area': 50}]}]} ]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas':[{'perimeter': {'area': 65}}]}
            ]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 7
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_successful_filter_max(self, reset_config):
        Config.set({'max': 90}, 'filter', 'area')
        expected = [
            fires.Fire({'id': '1', 'activity': [{'active_areas':[{'specified_points': [{'area': 45}]}]} ]}),
            fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}]}]} ]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas':[{'perimeter': {'area': 65}}]} ]}),
            fires.Fire({'id': '5', 'activity': [{'active_areas':[{'specified_points': [{'area': 85}]}]} ]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas':[{'specified_points': [{'area': 75}], 'perimeter': {'area': 90}}]}]}),
            fires.Fire({'id': '7', 'activity': [{'active_areas':[{'specified_points': [{'area': 50}]}]} ]}),
            fires.Fire({'id': '8', 'activity': [{'active_areas':[{'specified_points': [{'area': 30}]}]} ]}),
            fires.Fire({'id': '9', 'activity': [
                {'active_areas':[{'specified_points': [{'area': 45}]}]},
                {'active_areas':[{'specified_points': [{'area': 40}]}]}
            ]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas':[{'specified_points': [{'area': 45}]}]},
                {'active_areas':[{'perimeter': {'area': 65}}]}
            ]}),
            fires.Fire({'id': '11', 'activity': [{'active_areas':[{'specified_points': [{'area': 15}, {'area': 20}]}]} ]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 10
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_successful_filter_min_and_max(self, reset_config):
        # both min and max
        Config.set({'min': 52, 'max': 77.0}, 'filter', 'area')
        expected = [
            fires.Fire({'id': '3', 'activity': [{'active_areas':[{'specified_points': [{'area': 55}]}]} ]}),
            fires.Fire({'id': '4', 'activity': [{'active_areas':[{'perimeter': {'area': 65}}]} ]}),
            fires.Fire({'id': '6', 'activity': [{'active_areas':[{'specified_points': [{'area': 75}], 'perimeter': {'area': 90}}]}]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas':[{'perimeter': {'area': 65}}]}
            ]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 4
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # both min and max
        Config.set({'min': 65, 'max': 65.0}, 'filter', 'area')
        expected = [
            fires.Fire({'id': '4', 'activity': [{'active_areas':[{'perimeter': {'area': 65}}]} ]}),
            fires.Fire({'id': '10', 'activity': [
                {'active_areas':[{'perimeter': {'area': 65}}]}
            ]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 2
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

        # filter out the rest
        Config.set({'min': 76, 'max': 77.0}, 'filter', 'area')
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == sorted(self.fm.fires, key=lambda e: int(e.id))

        # call again with no fires
        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert [] == sorted(self.fm.fires, key=lambda e: int(e.id))


class TestFiresManagerFilterFiresByTime(object):

    def setup(self):
        self.fm = fires.FiresManager()
        self.init_fires = [
            fires.Fire({'id': '1', 'activity': [
                {'active_areas': [
                    # note this is midnight to midnight
                    {'start': '2019-01-01T17:00:00','end': "2019-01-02T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.0, 'lng': -80.0, "area": 90.0}]},
                    # note that this is midnight to noon
                    {'start': '2019-01-02T05:00:00','end': "2019-01-02T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.1, 'lng': -80.1, "area": 90.0}]}
                ]},
                {'active_areas': [
                    {'start': '2019-01-02T17:00:00','end': "2019-01-03T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.2, 'lng': -80.2, "area": 90.0}]}
                ]}
            ]}),
            fires.Fire({'id': '2', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-02T20:00:00','end': "2019-01-03T20:00:00","utc_offset": "-04:00",
                     'specified_points':[{'lat': 30.0, 'lng': -90.0, "area": 90.0},{'lat': 30.5, 'lng': -90.5, "area": 90.0}]}
                ]},
                {'active_areas': [
                    {'start': '2019-01-03T20:00:00','end': "2019-01-04T20:00:00","utc_offset": "-04:00",
                     'specified_points':[{'lat': 30.1, 'lng': -90.1, "area": 90.0},{'lat': 30.6, 'lng': -90.6, "area": 90.0}]}
                ]}
            ]})
        ]
        self.fm.fires = self.init_fires
        assert self.fm.num_fires == 2
        assert self.fm.num_locations == 7

    def test_invalid_config(self, reset_config):
        ## Failure situations
        scenarios = (
            # empty config
            ({}, fires.FireActivityFilter.MISSING_FILTER_CONFIG_MSG),
            # start and end not specified
            ({'foo': 'bar'}, fires.FireActivityFilter.SPECIFY_TIME_START_AND_OR_END_MSG),
            # invalid start
            ({'start': "sdf"},
                fires.FireActivityFilter.INVALID_TIME_START_OR_END_VAL.format('start')),
            # invalid end (with valid start)
            ({'start': "2019-01-01T00:00:00", "end": "sdfsd"},
                fires.FireActivityFilter.INVALID_TIME_START_OR_END_VAL.format('end')),
            # start after end
            ({'start': "2019-01-02T00:00:00", "end": "2019-01-01T00:00:00"},
                fires.FireActivityFilter.INVALID_START_AFTER_END)
        )
        for config, err_msg in scenarios:
            Config.set(config, 'filter', 'time')
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 2
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))
            assert e_info.value.args[0] == err_msg
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 2
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_invalid_fires(self, reset_config):
        Config.set({"start": "2019-01-01T00:00:00"}, 'filter', 'time')
        scenarios = (
            # active_area missing start
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{"end": "2019-01-02T17:00:00"}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # active_area missing end
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{"start": "2019-01-01T17:00:00"}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG),
            # active_area missing start and end
            (fires.Fire({'id': '1', 'activity': [{'active_areas':[{}]}]}),
             fires.FireActivityFilter.MISSING_FIRE_LOCATION_INFO_MSG)
        )
        for f, err_msg in scenarios:
            self.fm.fires = [f]
            # don't skip failures
            Config.set(False, 'filter', 'skip_failures')
            with raises(fires.FireActivityFilter.FilterError) as e_info:
                self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires
            assert e_info.value.args[0].index(err_msg) > 0
            # skip failures
            Config.set(True, 'filter', 'skip_failures')
            self.fm.filter_fires()
            assert self.fm.num_fires == 1
            assert [f] == self.fm.fires

    def test_noops(self, reset_config):
        scenarios = [
            {"start": "2019-01-01T00:00:00"},
            # start time is in UTC, so this doesn't filter anything,
            # since the earliest end time, 2019-01-02T17:00:00 (local),
            # is 2019-01-03T00:00:00 UTC
            {"start": "2019-01-02T20:00:00"},
            # this end time is local, so this doesn't filter anything,
            # since the latest start time is 2019-01-03T20:00:00 local
            {"end": "2019-01-03T22:00:00L"},
            {"start": "2019-01-01T00:00:00"},
            {"start": datetime.datetime(2019,1,1,0,0,0)},
            {"start": "2019-01-01T00:00:00", "end": "2019-01-05T00:00:00"},
            {"end": "2019-01-05T00:00:00"}
        ]

        for c in scenarios:
            Config.set(c,'filter', 'time')
            self.fm.filter_fires()
            assert self.fm.num_fires == 2
            assert self.fm.num_locations == 7
            assert self.init_fires == sorted(self.fm.fires, key=lambda e: int(e.id))


    def test_remove_first_two_aa_by_start(self, reset_config):
        Config.set({"start": "2019-01-03T00:00:00"},'filter', 'time')
        expected = [
            fires.Fire({'id': '1', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-02T17:00:00','end': "2019-01-03T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.2, 'lng': -80.2, "area": 90.0}]}
                ]}
            ]}),
            fires.Fire({'id': '2', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-02T20:00:00','end': "2019-01-03T20:00:00","utc_offset": "-04:00",
                     'specified_points':[{'lat': 30.0, 'lng': -90.0, "area": 90.0},{'lat': 30.5, 'lng': -90.5, "area": 90.0}]}
                ]},
                {'active_areas': [
                    {'start': '2019-01-03T20:00:00','end': "2019-01-04T20:00:00","utc_offset": "-04:00",
                     'specified_points':[{'lat': 30.1, 'lng': -90.1, "area": 90.0},{'lat': 30.6, 'lng': -90.6, "area": 90.0}]}
                ]}
            ]})
        ]
        self.fm.filter_fires()
        assert self.fm.num_fires == 2
        assert self.fm.num_locations == 5
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_but_first_aa_by_end(self, reset_config):
        Config.set({"end": "2019-01-02T07:00:00"},'filter', 'time')
        expected =  [
            fires.Fire({'id': '1', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-01T17:00:00','end': "2019-01-02T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.0, 'lng': -80.0, "area": 90.0}]},
                ]}
            ]})
        ]

        self.fm.filter_fires()
        assert self.fm.num_fires == 1
        assert self.fm.num_locations == 1
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_but_middle_aas_by_start_end(self, reset_config):
        Config.set({"start": "2019-01-03T00:00:00",
            "end": "2019-01-04T00:00:00"},'filter', 'time')
        expected =  [
            fires.Fire({'id': '1', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-02T17:00:00','end': "2019-01-03T17:00:00","utc_offset": "-07:00",
                     'specified_points':[{'lat': 40.2, 'lng': -80.2, "area": 90.0}]}
                ]}
            ]}),
            fires.Fire({'id': '2', 'activity': [
                {'active_areas': [
                    {'start': '2019-01-02T20:00:00','end': "2019-01-03T20:00:00","utc_offset": "-04:00",
                     'specified_points':[{'lat': 30.0, 'lng': -90.0, "area": 90.0},{'lat': 30.5, 'lng': -90.5, "area": 90.0}]}
                ]}
            ]})
        ]

        self.fm.filter_fires()
        assert self.fm.num_fires == 2
        assert self.fm.num_locations == 3
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_by_start_end(self, reset_config):
        Config.set({"start": "2019-01-07T00:00:00",
            "end": "2019-01-08T00:00:00"},'filter', 'time')
        expected =  []

        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert self.fm.num_locations == 0
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_by_start(self, reset_config):
        Config.set({"start": "2019-01-07T00:00:00"},'filter', 'time')
        expected =  []

        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert self.fm.num_locations == 0
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_by_start_specified_as_local(self, reset_config):
        Config.set({"start": "2019-01-04T22:00:00L"},'filter', 'time')
        expected =  []

        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert self.fm.num_locations == 0
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))

    def test_remove_all_by_end(self, reset_config):
        Config.set({"end": "2019-01-01T00:00:00"},'filter', 'time')
        expected =  []

        self.fm.filter_fires()
        assert self.fm.num_fires == 0
        assert self.fm.num_locations == 0
        assert expected == sorted(self.fm.fires, key=lambda e: int(e.id))
