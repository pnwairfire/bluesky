The ./bdyfiles subdirectory contains an ascii gridded land-use and
roughness length data for Hysplit.  The current file resolution
is 360x180 at 1 degree.  The upper left corner starts at 180W, 90N.
The files are read by routine sfcinp.f found in the hysplit source.
If not found, the model uses default constant values for land-use and
roughness length.

The structure of these files is defined in the ASCDATA.CFG file, which
defines the grid system and gives the directory location of the land-
use and roughness length files.

The ASCDATA.CFG file contains the following six records:

-90.0	-180.0	lat/lon of lower left corner (last record in file)
1.0	1.0	lat/lon spacing in degrees between data points
180	360	lat/lon number of data points
2		default land use category
0.2		default roughness length (meters)
'../bdyfiles/'	directory location of data files

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
times four bytes plus one additional byte for CR.  The sfcinp routine
is compiled to be able to handle a maximum file structure of 1440 data
points (global 360 deg x 4 points / deg).

Note if HYSPLIT is run from any other directory than the default
\working directory, ASCDATA.CFG must be present in the root directory
and point toward the \bdyfiles directory.
