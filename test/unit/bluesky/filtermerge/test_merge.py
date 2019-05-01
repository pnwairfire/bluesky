
##
## Tests for Merging
##
## TODO: unit test fires.FiresMerger directly
##

class TestFiresManagerMergeFires(object):

    def test_no_fires(self, reset_config):
        fm = fires.FiresManager()
        assert fm.num_fires == 0
        assert fm.fires == []
        fm.merge_fires()
        assert fm.num_fires == 0
        assert fm.fires == []

    def test_one_fire(self, reset_config):
        fm = fires.FiresManager()
        f = fires.Fire({'id': '1'})
        fm.fires = [f]
        assert fm.num_fires == 1
        assert fm.fires == [f]
        fm.merge_fires()
        assert fm.num_fires == 1
        assert fm.fires == [f]

    def test_none_to_merge(self, reset_config):
        fm = fires.FiresManager()
        f = fires.Fire({'id': '1'})
        f2 = fires.Fire({'id': '2'})
        fm.fires = [f, f2]
        assert fm.num_fires == 2
        assert fm.fires == [f, f2]
        fm.merge_fires()
        assert fm.num_fires == 2
        assert fm.fires == [f, f2]

    def test_simple(self, reset_config):
        fm = fires.FiresManager()
        f = fires.Fire({'id': '1'})
        f2 = fires.Fire({'id': '1'})
        fm.fires = [f, f2]
        fm.num_fires == 1
        assert dict(fm.fires[0]) == {
            'id': '1',
            'fuel_type': fires.Fire.DEFAULT_FUEL_TYPE,
            'type': fires.Fire.DEFAULT_TYPE
        }

    def test_invalid_keys(self, reset_config):
        # test in both skip and no-skip modes
        for s in (True, False):
            # i.e. top-level location is old structure
            fm = fires.FiresManager()
            Config.set(s, 'merge', 'skip_failures')
            f = fires.Fire({'id': '1', 'location': {'area': 132}})
            f2 = fires.Fire({'id': '1', 'location': {'area': 132}})
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert fm.num_fires == 2
                assert e_info.value.args[0].index(fires.FiresMerger.INVALID_KEYS_MSG) > 0
            else:
                fm.merge_fires()
                assert fm.num_fires == 2
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.id))

    def test_activity_for_only_one_fire(self, reset_config):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            Config.set(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1'
            })
            f2 = fires.Fire({
                'id': '1',
                "activity":[
                    {
                        "active_areas": [
                            {
                                "start": "2014-05-27T17:00:00",
                                "end": "2014-05-28T17:00:00",
                                'specified_points': [
                                    {'area': 132, 'lat': 45.0, 'lng': -120.0}
                                ]
                            }
                        ]
                    }
                ]
            })
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert fm.num_fires == 2
                assert e_info.value.args[0].index(
                    fires.FiresMerger.ACTIVITY_FOR_BOTH_OR_NONE_MSG) > 0
            else:
                fm.merge_fires()
                assert fm.num_fires == 2
                assert [f, f2] == sorted(fm.fires, key=lambda e: int('activity' in e))

    def test_overlapping_activity(self, reset_config):
        # TODO: implemented once check is in place
        pass

    def test_different_event_ids(self, reset_config):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            Config.set(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                "event_of":{
                    "id": "ABC"
                },
                # activity just used for assertion, below
                "activity": [{
                    "active_areas": [{'specified_points': [{'area': 123}]}]
                }]
            })
            f2 = fires.Fire({
                'id': '1',
                "event_of":{
                    "id": "SDF"
                },
                # activity just used for assertion, below
                "activity": [{
                    "active_areas": [{'specified_points': [{'area': 456}]}]
                }]
            })
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert fm.num_fires == 2
                assert e_info.value.args[0].index(fires.FiresMerger.EVENT_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert fm.num_fires == 2
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.activity[0]['location']['area']))

    def test_different_fire_and_fuel_type(self, reset_config):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            Config.set(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural",
                # activity just used for assertion, below
                "activity": [{
                    "active_areas": [{'specified_points': [{'area': 123}]}]
                }]
            })
            f2 = fires.Fire({
                'id': '1',
                "type": "wf",
                "fuel_type": "natural",
                # activity just used for assertion, below
                "activity": [{
                    "active_areas": [{'specified_points': [{'area': 456}]}]
                }]
            })
            fm.fires = [f, f2]
            assert fm.num_fires == 2

            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert fm.num_fires == 2
                assert e_info.value.args[0].index(fires.FiresMerger.FIRE_TYPE_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert fm.num_fires == 2
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.activity[0]['location']['area']))

            f2.type = f.type
            f2.fuel_type = "activity"
            fm.fires = [f, f2]
            assert fm.num_fires == 2
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert fm.num_fires == 2
                assert e_info.value.args[0].index(fires.FiresMerger.FUEL_TYPE_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert fm.num_fires == 2
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.activity[0]['location']['area']))

    def test_merge_mixed_success_no_activity(self, reset_config):
        fm = fires.FiresManager()
        #Config.set(True, 'merge', 'skip_failures')
        f = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural"
        })
        f2 = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural"
        })
        f3 = fires.Fire({
            'id': '2',
            "type": "rx",
            "fuel_type": "natural"
        })
        fm.fires = [f, f2, f3]
        assert fm.num_fires == 3
        fm.merge_fires()
        expected = [
            fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural"
            }),
            fires.Fire({
                'id': '2',
                "type": "rx",
                "fuel_type": "natural"
            })
        ]
        assert fm.num_fires == 2
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

    def test_merge_mixed_success(self, reset_config):
        fm = fires.FiresManager()
        #Config.set(True, 'merge', 'skip_failures')
        f = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2014-05-28T17:00:00",
                            "end": "2014-05-29T17:00:00",
                            'specified_points': [
                                {'area': 90, 'lat': 45.0, 'lng': -120.0}
                            ]
                        },
                        {
                            "start": "2014-05-29T17:00:00",
                            "end": "2014-05-30T17:00:00",
                            'specified_points': [
                                {'area': 90, 'lat': 46.0, 'lng': -120.0}
                            ]
                        }
                    ]
                }
            ]
        })
        f2 = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2014-05-27T17:00:00",
                            "end": "2014-05-28T17:00:00",
                            'specified_points': [
                                {'area': 10, 'lat': 45.0, 'lng': -120.0}
                            ]
                        }
                    ]
                }
            ]
        })
        f3 = fires.Fire({
            'id': '2',
            "type": "rx",
            "fuel_type": "natural",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2014-05-27T17:00:00",
                            "end": "2014-05-30T17:00:00",
                            'specified_points': [
                                {'area': 132, 'lat': 45.0, 'lng': -120.0}
                            ]
                        }
                    ]
                }
            ]
        })
        fm.fires = [f, f2, f3]
        assert fm.num_fires == 3
        fm.merge_fires()
        assert fm.num_fires == 2
        expected = [
            fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural",
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2014-05-27T17:00:00",
                                "end": "2014-05-28T17:00:00",
                                'specified_points': [
                                    {'area': 10, 'lat': 45.0, 'lng': -120.0}
                                ]
                            },
                            {
                                "start": "2014-05-28T17:00:00",
                                "end": "2014-05-29T17:00:00",
                                'specified_points': [
                                    {'area': 90, 'lat': 45.0, 'lng': -120.0}
                                ]
                            },
                            {
                                "start": "2014-05-29T17:00:00",
                                "end": "2014-05-30T17:00:00",
                                'specified_points': [
                                    {'area': 90, 'lat': 46.0, 'lng': -120.0}
                                ]
                            }
                        ]
                    }
                ]
            }),
            fires.Fire({
                'id': '2',
                "type": "rx",
                "fuel_type": "natural",
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2014-05-27T17:00:00",
                                "end": "2014-05-30T17:00:00",
                                'specified_points': [
                                    {'area': 132, 'lat': 45.0, 'lng': -120.0}
                                ]
                            }
                        ]
                    }
                ]
            })
        ]
        actual = sorted(fm.fires, key=lambda e: int(e.id))
        assert expected == actual
