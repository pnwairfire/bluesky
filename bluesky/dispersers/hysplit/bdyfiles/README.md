The ./bdyfiles subdirectory contains an ascii gridded land-use and 
roughness length data for Hysplit.  The terrain file is used by
some of the programs in /data2arl. The current file resolution
is 360x180 at 1 degree.  The upper left corner starts at 180W, 90N.
The files are read by library subroutine SFCINP.  If not found the 
model uses default constant values for land-use and roughness length.

The structure of these files is defined in the ASCDATA.CFG file, which
defines the grid system and gives the directory location of the land-
use and roughness length files. The ASCDATA.CFG file should be located
in the model's startup or root directory for non-standard directory 
installations. In these situations the last line in the file should be  
modified to reflect the true path of the /bdyfiles directory.

The ASCDATA.CFG file contains the following six records:

-90.0   -180.0  lat/lon of lower left corner (last record in file)
1.0     1.0     lat/lon spacing in degrees between data points
180     360     lat/lon number of data points
2               default land use category
0.2             default roughness length (meters)
'../bdyfiles/'  directory location of data files

These files may be replaced by higher resolution user created files.
Note that the first data point on the first record is assumed to be
centered at 179.5W and 89.5N, so that from the northwest corner the 
the data goes eastward and then southward. User supplied files should 
define roughness length (cm - F4) and the following land use 
categories (I4).

1-urban
2-agricultural
3-dry range
4-deciduous
5-coniferous
6-mixed forest
7-water
8-desert
9-wetlands
10-mixed range
11-rocky

The record length of the file should be the number of longitude values
times four bytes plus one additional byte for CR. 

An additional dataset with a 0.5 degree resolution (720x360) is included under
the .\bdyfiles0p5 directory. To use this dataset replace the ASCDATA.CFG
from the .\bdyfiles0p5 in the \working directory.

Note if HYSPLIT is run from any other directory than the default
\working directory, ASCDATA.CFG must be present in the root directory
and point toward the boundary files directory. Otherwise, if using the
0.5 degree resolution files, ASCDATA.CFG needs to point toward the directory
containing the bdyfiles0p5 files.


The ./legacy subdirectory contains the old files of
LANDUSE.ASC, ROUGLEN.ASC, and TERRAIN.ASC for 1 deg and 0.5 deg.

An additional dataset with a 0.1 degree resolution (1800x3600) is included
under the \bdyfiles0p1 directory. To use this dataset replace the ASCDATA.CFG
from the \bdyfiles0p1 in the \working directory.

if using the 0.1 degree resolution files, ASCDATA.CFG needs to point toward
the directory directory contain the boundary files.

