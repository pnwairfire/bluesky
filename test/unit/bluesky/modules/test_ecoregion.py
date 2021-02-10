"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import copy

from py.test import raises

from bluesky.config import Config
from bluesky.models.fires import FiresManager, Fire
from bluesky.modules import ecoregion
from bluesky.exceptions import BlueSkyGeographyValueError

FIRE_NO_ACTIVITY = Fire({
    "id": "SF11C14225236095807750"
})

FIRE = Fire({
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2015-01-20T17:00:00",
                    "end": "2015-01-21T17:00:00",
                    "utc_offset": "-07:00",
                    "specified_points": [
                        {
                            "lat": 45,
                            "lng": -119,
                            "area": 123
                        },
                        {
                            "lat": 45.3,
                            "lng": -119.2,
                            "area": 123
                        }
                    ]
                },
                {
                    "pct": 40,
                    "start": "2015-01-21T17:00:00", # SAME TIME WINDOW
                    "end": "2015-01-22T17:00:00",
                    "utc_offset": "-07:00",
                    "perimeter": {
                        "polygon": [
                            [-121.45, 47.43],
                            [-121.39, 47.43],
                            [-121.39, 47.40],
                            [-121.45, 47.40],
                            [-121.45, 47.43]
                        ]
                    }
                }
            ]
        }
    ]
})


class TestEcoRegionRun(object):

    def test_no_fires(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fires": []
        })
        # just making sure no exception is raised
        ecoregion.run(fm)

    def test_one_fire_with_no_activity(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE_NO_ACTIVITY)]
        })
        # just making sure no exception is raised
        ecoregion.run(fm)

    def test_one_fire_with_activity(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        ecoregion.run(fm)
        assert len(fm.fires) == 1
        assert fm.failed_fires == None
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][1]['perimeter']['ecoregion'] == 'western'

    def test_one_fire_with_activity_with_ignored_default(self, reset_config):
        Config().set('boreal', 'ecoregion', 'default')
        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        ecoregion.run(fm)
        assert len(fm.fires) == 1
        assert fm.failed_fires == None
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][1]['perimeter']['ecoregion'] == 'western'

    def test_one_fire_invalid_lat_no_raise(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['lng'] = -200.0
        ecoregion.run(fm)
        assert len(fm.fires) == 1
        assert fm.failed_fires == None
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert 'ecoregion' not in fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]
        assert fm.fires[0]['activity'][0]['active_areas'][1]['perimeter']['ecoregion'] == 'western'

    def test_one_fire_invalid_lat_exception_not_skipped_but_caught(self, reset_config):
        Config().set(True, 'skip_failed_fires')
        Config().set(False, 'ecoregion', 'skip_failures')

        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['lng'] = -200.0
        ecoregion.run(fm)
        assert len(fm.fires) == 0
        assert len(fm.failed_fires) == 1
        assert fm.failed_fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert 'ecoregion' not in fm.failed_fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]
        assert 'ecoregion' not in fm.failed_fires[0]['activity'][0]['active_areas'][1]['perimeter']

    def test_one_fire_invalid_lat_exception_not_skipped_and_not_caught(self, reset_config):
        Config().set(False, 'skip_failed_fires')
        Config().set(False, 'ecoregion', 'skip_failures')

        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['lng'] = -200.0
        with raises(BlueSkyGeographyValueError) as e_info:
            ecoregion.run(fm)
        assert e_info.value.args[0].startswith('Invalid lat,lng:')

    def test_one_fire_invalid_lat_exception_with_default(self, reset_config):
        Config().set(False, 'skip_failed_fires')
        Config().set(False, 'ecoregion', 'skip_failures')
        Config().set('boreal', 'ecoregion', 'default')

        fm = FiresManager()
        fm.load({
            "fires": [copy.deepcopy(FIRE)]
        })
        fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['lng'] = -200.0
        ecoregion.run(fm)
        assert len(fm.fires) == 1
        assert fm.failed_fires == None
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['ecoregion'] == 'boreal'
        assert fm.fires[0]['activity'][0]['active_areas'][1]['perimeter']['ecoregion'] == 'western'
