import os
import pytest
import tempfile

from bluesky.trajectories.hysplit import load

ONE_LOC_ONE_HEIGHT_TDUMP = """         1     1
        AWRF    19     6    10    12     0
         6 FORWARD  OMEGA
      2019     6    10    12   37.910 -119.762    10.0
      2019     6    10    12   39.350 -120.040    10.0
         7 PRESSURE THETA    AIR_TEMP RAINFALL MIXDEPTH RELHUMID SUN_FLUX
         1     1    19     6    10    12     0     0     0.0   37.910 -119.762     10.0    841.3    300.8    286.2      0.0     13.8     42.3      0.1
         1     1    19     6    10    13     0     1     1.0   37.836 -119.930      0.0    893.4    299.5    290.0      0.0    452.2     41.3     10.4
        ....

"""

TWO_LOC_THREE_HEIGHT_TDUMP = """         1     1
        AWRF    19     6    10    12     0
         6 FORWARD  OMEGA
      2019     6    10    12   37.910 -119.762    10.0
      2019     6    10    12   37.910 -119.762   100.0
      2019     6    10    12   37.910 -119.762  1000.0
      2019     6    10    12   39.350 -120.040    10.0
      2019     6    10    12   39.350 -120.040   100.0
      2019     6    10    12   39.350 -120.040  1000.0
         7 PRESSURE THETA    AIR_TEMP RAINFALL MIXDEPTH RELHUMID SUN_FLUX
         1     1    19     6    10    12     0     0     0.0   37.910 -119.762     10.0    841.3    300.8    286.2      0.0     13.8     42.3      0.1
         2     1    19     6    10    12     0     0     0.0   37.910 -119.762    100.0    832.5    303.3    287.8      0.0     13.8     46.3      0.1
         3     1    19     6    10    12     0     0     0.0   37.910 -119.762   1000.0    747.6    311.1    286.2      0.0     13.8     30.9      0.1
         4     1    19     6    10    12     0     0     0.0   39.350 -120.040     10.0    823.6    300.8    284.6      0.0      3.3     41.9      0.5
         5     1    19     6    10    12     0     0     0.0   39.350 -120.040    100.0    814.7    302.4    285.2      0.0      3.2     42.7      0.5
         6     1    19     6    10    12     0     0     0.0   39.350 -120.040   1000.0    731.4    310.6    284.0      0.0      3.2     31.7      0.5
         1     1    19     6    10    13     0     1     1.0   37.836 -119.930      0.0    893.4    299.5    290.0      0.0    452.2     41.3     10.4
         2     1    19     6    10    13     0     1     1.0   37.836 -119.929      0.0    893.2    299.5    290.0      0.0    440.7     41.4     10.4
         3     1    19     6    10    13     0     1     1.0   37.877 -119.731    856.9    736.5    311.5    285.4      0.0    568.6     22.7      8.6
         4     1    19     6    10    13     0     1     1.0   39.373 -120.022     74.5    809.6    302.3    284.6      0.0    114.6     42.3     31.4
         5     1    19     6    10    13     0     1     1.0   39.390 -120.036    154.3    800.9    303.3    284.6      0.0     49.9     40.8     31.6
         6     1    19     6    10    13     0     1     1.0   39.385 -120.044   1033.7    722.7    311.0    283.4      0.0     49.9     34.4     31.2
        ....

"""

class test_output_file():
    def __init__(self, contents):
        self._contents = contents.encode()

    def __enter__(self):
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.write(self._contents)
        self.f.close()
        return self.f.name

    def __exit__(self, exc_type, exc_value, traceback):
        os.unlink(self.f.name)

class TestOutputLoader():

    def test_one_location_one_height(self):
        with test_output_file(ONE_LOC_ONE_HEIGHT_TDUMP) as filename:
            config = {
                'output_file_name': os.path.basename(filename),
                'heights': [10]
            }
            locations = [{}]

            loader = load.OutputLoader(config)
            loader.load("2019-06-10T12:00:00Z", os.path.dirname(filename), locations)

            expected = [{
                "trajectories":{
                    "model": "hysplit",
                    "lines": [
                        {
                            "start": "2019-06-10T12:00:00Z",
                            "height": 10,
                            "points": [
                                [37.910, -119.762, 10.0],
                                [37.836, -119.930, 0.0]
                            ]
                        }
                    ]
                }
            }]

            assert locations == expected

    def test_two_locations_three_heights(self):
        with test_output_file(TWO_LOC_THREE_HEIGHT_TDUMP) as filename:
            config = {
                'output_file_name': os.path.basename(filename),
                'heights': [10, 100, 1000]
            }
            locations = [{}, {}]

            loader = load.OutputLoader(config)
            loader.load("2019-06-10T12:00:00Z", os.path.dirname(filename), locations)

            expected = [
                {
                    "trajectories":{
                        "model": "hysplit",
                        "lines": [
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 10,
                                "points": [
                                    [37.910, -119.762, 10.0],
                                    [37.836, -119.930, 0.0]
                                ]
                            },
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 100,
                                "points": [
                                    [37.910, -119.762, 100.0],
                                    [37.836, -119.929, 0.0]
                                ]
                            },
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 1000,
                                "points": [
                                    [37.910, -119.762, 1000.0],
                                    [37.877, -119.731, 856.9]
                                ]
                            }
                        ]
                    }
                },
                {
                    "trajectories":{
                        "model": "hysplit",
                        "lines": [
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 10,
                                "points": [
                                    [39.350, -120.040, 10.0],
                                    [39.373, -120.022, 74.5]
                                ]
                            },
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 100,
                                "points": [
                                    [39.350, -120.040, 100.0],
                                    [39.390, -120.036, 154.3]
                                ]
                            },
                            {
                                "start": "2019-06-10T12:00:00Z",
                                "height": 1000,
                                "points": [
                                    [39.350, -120.040, 1000.0],
                                    [39.385, -120.044, 1033.7]
                                ]
                            }
                        ]
                    }
                }
            ]

            assert locations == expected
