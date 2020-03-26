import re
import os

class OutputLoader(object):
    """Loads data from output file produced by hysplit trajectories

    Output file format (from a run with one location, starting at hour 0,
    with four start heights, 100, 500, 1000, 2000)

         1     1
         NAM    15     8     5     0     0
         4 FORWARD  OMEGA
      2015     8     5     0   49.000 -119.000   100.0
      2015     8     5     0   49.000 -119.000   500.0
      2015     8     5     0   49.000 -119.000  1000.0
      2015     8     5     0   49.000 -119.000  2000.0
         1 PRESSURE
         1     1    15     8     5     0     0     0     0.0   49.000 -119.000    100.0    992.7
         2     1    15     8     5     0     0     0     0.0   49.000 -119.000    500.0    946.6
         3     1    15     8     5     0     0     0     0.0   49.000 -119.000   1000.0    891.6
         4     1    15     8     5     0     0     0     0.0   49.000 -119.000   2000.0    789.4
         1     1    15     8     5     1     0     1     1.0   49.059 -118.915     94.3    954.7
         2     1    15     8     5     1     0     1     1.0   49.059 -118.905    501.9    909.9
         3     1    15     8     5     1     0     1     1.0   49.064 -118.902   1013.1    856.1
         4     1    15     8     5     1     0     1     1.0   49.100 -118.893   2090.1    750.2
         ....

    Another example output, with more columns (from a run  with one location
    starting at hour 6, with only one start height, 100)

         1     1
         NAM    15     8     5     0     0
         1 FORWARD  OMEGA
      2015     8     5     6   50.000 -120.000   100.0
         7 PRESSURE THETA    AIR_TEMP RAINFALL MIXDEPTH RELHUMID SUN_FLUX
         1     1    15     8     5     6     0     6     0.0   50.000 -120.000    100.0    847.8    298.8    285.0      0.0    479.6     54.6      0.0
         1     1    15     8     5     7     0     7     1.0   50.006 -119.719      0.0    880.9    298.3    287.7      0.0    394.6     48.0      0.0
         1     1    15     8     5     8     0     8     2.0   50.018 -119.568      0.0    899.3    297.5    288.6      0.0    402.2     45.9      0.0
         ....

    Another example (from a run with 2 locations, starting at hour 0, with
    3 heights, 10, 100, 1000)

         1     1
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


    The loaded trajectory data is added to each location, structured as follows:

    {
        ...
        "trajectories": {
            "model": "hysplit",
            "lines": [
                {
                    "start": "2019-03-20T00:00:00Z",
                    "height": 100,
                    "points": [
                        (35.0, -120, 100)
                    ]
                }
            ]
        }
    }
    """

    def __init__(self, config, locations):
        self._config = config
        self._locations = locations

    def load(self, start, working_dir):
        self._initialize_locations(start)
        filename = os.path.join(working_dir, self._config['output_file_name'])
        with open(filename, 'r') as f:
            num_locations = len(self._locations)
            num_heights = len(self._config['heights'])
            for line in f:
                parts = re.split('\s+', line.strip())
                if parts >= 13:
                    set_idx = int(parts[0]) - 1
                    l_idx = int(set_idx / num_heights)
                    h_idx = set_idx % 3
                    self._locations[l_idx]['trajectories']['lines'][h_idx]['line'].append(
                        float(parts[9]), float(parts[10]), float(parts[11])
                    )

    def _initialize_locations(self, start):
        for loc in self._locations:
            if not 'trajectories' in self._locations:
                loc['trajectories'] = {
                    "model": hysplit,
                    "lines": []
                }
            for h in self._config['heights']:
                loc['trajectories']['lines'].append({
                    "start": start,
                    "height": h,
                    "points": []
                })