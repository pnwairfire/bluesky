import os

class OutputLoader(object):
    """Loads output file produced by hysplit trajectories

    Output file format (from a run starting at hour 0, with four start
    heights, 100, 500, 1000, 2000)
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

    Another example output, with more columns (from a run starting
    at hour 6, with only one start height, 100)

         1     1
         NAM    15     8     5     0     0
         1 FORWARD  OMEGA
      2015     8     5     6   50.000 -120.000   100.0
         7 PRESSURE THETA    AIR_TEMP RAINFALL MIXDEPTH RELHUMID SUN_FLUX
         1     1    15     8     5     6     0     6     0.0   50.000 -120.000    100.0    847.8    298.8    285.0      0.0    479.6     54.6      0.0
         1     1    15     8     5     7     0     7     1.0   50.006 -119.719      0.0    880.9    298.3    287.7      0.0    394.6     48.0      0.0
         1     1    15     8     5     8     0     8     2.0   50.018 -119.568      0.0    899.3    297.5    288.6      0.0    402.2     45.9      0.0
         ....
    """

    def __init__(config):
        self._config = config

    def load(working_dir):
        with open(os.path.join(working_dir, config['output_file_name']), 'r') as f:
            pass
