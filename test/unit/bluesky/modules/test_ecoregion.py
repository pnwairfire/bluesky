"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.models.fires import FiresManager, Fire
from bluesky.modules import ecoregion



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

    def test_no_fires(self):
        fm = FiresManager()
        fm.load({
            "fires": []
        })
        # just making sure no exception is raised
        ecoregion.run(fm)

    def test_one_fire_with_no_activity(self):
        fm = FiresManager()
        fm.load({
            "fires": [FIRE_NO_ACTIVITY]
        })
        # just making sure no exception is raised
        ecoregion.run(fm)

    def test_one_fire_with_activity(self):
        fm = FiresManager()
        fm.load({
            "fires": [FIRE]
        })
        ecoregion.run(fm)
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][0]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][0]['specified_points'][1]['ecoregion'] == 'western'
        assert fm.fires[0]['activity'][0]['active_areas'][1]['perimeter']['ecoregion'] == 'western'
        # Nothing to check. just make sure no error
