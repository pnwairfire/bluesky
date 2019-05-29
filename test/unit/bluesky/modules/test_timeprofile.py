"""Unit tests for bluesky.modules.timeprofile"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models import fires
from bluesky.modules import timeprofile


class TestTimeprofilingRunFire(object):

    ##
    ## Failure cases
    ##

    def test_4_hourly_fractions_and_multiple_active_areas(self, reset_config):
        # setting
        hourly_fractions = {
            "flaming": [0.8, 0.1, 0.1],
            "smoldering": [0.8, 0.1, 0.1],
            "area_fraction": [0.8, 0.1, 0.1],
            "residual": [0.8, 0.1, 0.1]
        }
        #Config.set(hourly_fractions, "timeprofile","hourly_fractions")

        fire = fires.Fire({
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T17:00:00",
                            "end": "2015-08-05T17:00:00"
                        },
                        {
                            "start": "2015-08-05T17:00:00",
                            "end": "2015-08-06T17:00:00"
                        }
                    ]
                }
            ]
        })
        with raises(BlueSkyConfigurationError) as e_info:
            timeprofile._run_fire(hourly_fractions, fire)
        assert e_info.value.args[0] == timeprofile.NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG

        fire = fires.Fire({
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T17:00:00",
                            "end": "2015-08-05T17:00:00",
                        }
                    ]
                },
                {
                    "active_areas": [
                        {
                            "start": "2015-08-05T17:00:00",
                            "end": "2015-08-06T17:00:00"
                        }
                    ]
                }
            ]
        })
        with raises(BlueSkyConfigurationError) as e_info:
            timeprofile._run_fire(hourly_fractions, fire)
        assert e_info.value.args[0] == timeprofile.NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG

    def test_no_active_areas(self, reset_config):
        fire = fires.Fire({
            "id": "slijlfdsljfsdkljf"
        })
        with raises(ValueError) as e_info:
            timeprofile._run_fire(None, fire)
        assert e_info.value.args[0] == timeprofile.MISSING_ACTIVITY_AREA_MSG

        fire = fires.Fire({
            "id": "slijlfdsljfsdkljf",
            "activity": [
                {
                    "active_areas": []
                }
            ]
        })
        with raises(ValueError) as e_info:
            timeprofile._run_fire(None, fire)
        assert e_info.value.args[0] == timeprofile.MISSING_ACTIVITY_AREA_MSG

    def test_active_area_missing_start(self, reset_config):
        fire = fires.Fire({
            "id": "slijlfdsljfsdkljf",
            "activity": [
                {
                    "active_areas": [
                        {
                            "specified_points": [
                                {
                                    "lng": -121.3990506,
                                    "lat": 47.4316976,
                                    "area": 20000.0,
                                    "fuelbeds": [
                                        {
                                            "pct": 45.0,
                                            "fccs_id": "41"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
        })
        with raises(ValueError) as e_info:
            timeprofile._run_fire(None, fire)
        assert e_info.value.args[0] == timeprofile.INSUFFICIENT_ACTIVITY_INFP_MSG


    ##
    ## Valid cases
    ##

    def test_one_active_area(self, reset_config):
        fire = fires.Fire({
            "id": "SF11C14225236095807750",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-01-20T00:00:00",
                            "end": "2015-01-20T02:00:00",
                        }
                    ]
                }
            ]
        })
        expected = {
            "2015-01-20T00:00:00": {
                "flaming": 0.5,
                "area_fraction": 0.5,
                "residual": 0.5,
                "smoldering": 0.5
            },
            "2015-01-20T01:00:00": {
                "flaming": 0.5,
                "area_fraction": 0.5,
                "residual": 0.5,
                "smoldering": 0.5
            }
        }
        timeprofile._run_fire(None, fire)
        actual = fire['activity'][0]['active_areas'][0]['timeprofile']
        assert actual == expected