"""Unit tests for bluesky.modules.timeprofiling"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models import fires
from bluesky.modules import timeprofiling


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
        #Config.set(hourly_fractions, "timeprofiling","hourly_fractions")

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
            timeprofiling._run_fire(hourly_fractions, fire)
        assert e_info.value.args[0] == timeprofiling.NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS

        fire_2 = fires.Fire({
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
            timeprofiling._run_fire(hourly_fractions, fire_2)
        assert e_info.value.args[0] == timeprofiling.NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS
