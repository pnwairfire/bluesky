import os

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError

class ControlFileWriter(object):
    """Write CONTROL file to run hysplit trajectories

     CONTROL file format:

        00 00 00 00            # Y M D H [min] starting time (UTC) (all zeros means use beginning of met file)
        3                      # number of trajectories STARTING AT THE SAME TIME (see advanced GUI menu)
        40.0 -90.0   10.0      # lat lon height (above ground level)
        40.0 -90.0  500.0      # lat lon height (above ground level)
        40.0 -90.0 1000.0      # lat lon height (above ground level)
        12                     # total run time (hours)
        0                      # vertical motion (0 = from met file)
        10000.0                # top of model domain (trajectories end above this)
        1                      # number of simultaneous met files
        ./                     # met grid directory
        oct1618.BIN            # met grid file (ARL format)
        ./                     # output directoroy
        tdump                  # output file

     Example content:

         2016 05 11 00
          7
         66.00 -141.00 500.000
         66.00 -141.00 1000.000
         66.00 -141.00 1500.000
         66.00 -141.00 2000.000
         66.00 -141.00 2500.000
         66.00 -141.00 3000.000
         66.00 -141.00 5000.000
         24
         0
         10000.0
         1
         ./
         gfs_bc_2016051100.arl
         ./
         gfs_NorthAmericaFine_2016051100_000.traj
    """

    def __init__(config):
        self._config = config

    def write(locations, start, num_hours, working_dir):

        with open(os.path.join(working_dir, 'CONTROL'), 'w') as f:
            f.write(start.strftime("%Y %m %d %H\n"))

            # TODO: is this correct?
            num_trajectries = len(locations) * len(self._config['heights'])
            f.write("{}\n".format(num_trajectries))

            for loc in locations:
                for h in self._config['heights']:
                    f.write("{} {} {}\n".format(loc.lat, loc.lng, h))

            f.write("{}\n".format(num_hours))
            f.write("{}\n".format(self._config['vertical_motion']))
            f.write("{}\n".format(self._config['top_of_model_domain']))
            f.write("{}\n".format(self._config['num_simultaneous_met_files']))
            f.write("./\n")  # met grid directory
            f.write("oct1618.BIN\n")  # met grid file (ARL format)
            f.write("./\n")  # output directoroy
            f.write("{}\n".format(self._config['output_file_name']))
