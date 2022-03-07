## Input Data

The top level input data fields that bsp recognizes are: ```run_id```,
```today```, and ```fires```.

### 'run_id'

Run identifier. If not defined, bluesky will generate a GUID.

### 'today'

The day of the run.  Configuration settings are relative to this date.

### 'fires' Fields

The top level 'fires' array has data added to it's elements as it
moves through the pipeline of modules.  Each module has its own set of
required and optional fields that it uses, so that the set of data needed
for each fire depends on the modules to be run. Generally, the further you
are along the pipeline of modules, the more data you need.  (Note, however,
that some data required by earlier modules can be dropped when you pipe the
fire data into downstream modules.)

Note that list/array fields, listed below, are denoted with square brackets.
e.g. ['active_areas']

##### load

(no required fields)

##### merge

TODO: fill in this section...

##### filter

TODO: fill in this section...

##### fuelbeds

Looking up fuelbeds requires either point data:

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lat'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lng'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'area'*** -- *required* (if not specifying perimeter) --

or perimeter data

 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'polygon'*** -- *required* (if not specifying point data) --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'area'*** -- *optional* (if not specifying point data) -- filled in by fuelbeds module if not specified

Other fields

 - ***['fires'] > ['activity'] > ['active_areas'] > 'state'*** -- *required* if AK -- used to determine which FCCS version to use

##### consumption

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuelbeds'*** -- *required* -- array of fuelbeds objects, each containing 'fccs_id' and 'pct'
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'area'*** -- *required* -- fire's total area
 - ***['fires'] > ['activity'] > ['active_areas'] > 'ignition_start'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'ignition_end'*** -- *required* --


The following can be defined either under 'specified_points' or 'perimeter'
objects, or directly under the parent 'active_areas' object

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'ecoregion'*** -- *required*
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'slope'*** -- *optional* -- default: 5
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'windspeed'*** -- *optional* -- default: 6
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'days_since_rain' or 'rain_days'*** -- *optional* -- default: 10;
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fm_type'*** -- *optional* -- default: "MEAS-Th"
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuel_moisture_10hr_pct' or 'moisture_10hr'*** -- *optional* -- default: 50
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuel_moisture_1000hr_pct' or 'moisture_1khr'*** -- *optional* -- default: 30
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuel_moisture_duff_pct' or 'moisture_duff'*** -- *optional* -- default: 75
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuel_moisture_litter_pct' or 'moisture_litter'*** -- *optional* -- default: 16
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'canopy_consumption_pct'*** -- *optional* -- default: 0
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'shrub_blackened_pct'*** -- *optional* -- default: 50
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'pile_blackened_pct'*** -- *optional* -- default: 0
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'output_units'*** -- *optional* -- default: "tons_ac"
 - ***['fires'] > 'type'*** -- *optional* -- fire type ('rx' vs. 'wildfire'); default: 'wildfire'
 - ***['fires'] > 'fuel_type'*** -- *optional* -- fuel type ('natural', 'activity', or 'piles'); default: 'natural'

###### if an 'rx' burn:

The following can be defined either under 'specified_points' or 'perimeter'
objects, or directly under the parent 'active_areas' object

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'days_since_rain'*** -- *required* -- default: 1
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'slope'*** -- *optional* -- default: 5
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'windspeed'*** -- *optional* -- default: 5
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fuel_moisture_10hr_pct'*** -- *optional* -- default: 50
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'fm_type'*** -- *optional* -- default: "MEAS-Th"

##### emissions

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > ['fuelbeds'] > 'consumption'*** -- *required* --

##### findmetdata

 - ***['fires'] > ['activity'] > ['active_areas'] > 'start' *** -- *required* if time_window isn't specified in the config'start', 'end'
 - ***['fires'] > ['activity'] > ['active_areas'] > 'end' *** -- *required* if time_window isn't specified in the config'start', 'end'

##### localmet

 - ***'met' > 'files'*** -- *required* -- array of met file objects, each containing 'first_hour', 'last_hour', and 'file' keys

localmet requires either point data:

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lat'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lng'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'area'*** -- *required* (if not specifying perimeter) --

or perimeter data

 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'polygon'*** -- *required* (if not specifying point data) --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'area'*** -- *required* (if not specifying point data) --

The following can be defined either under 'specified_points' or 'perimeter'
objects, or directly under the parent 'active_areas' object

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'utc_offset'*** -- *required*

##### timeprofile

 - ***['fires'] > ['activity'] > ['active_areas'] > 'start' *** -- *required* if time_window isn't specified in the config'start', 'end'
 - ***['fires'] > ['activity'] > ['active_areas'] > 'end' *** -- *required* if time_window isn't specified in the config'start', 'end'

##### plumerise

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'area'*** -- *required* --

###### If running FEPS model

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'area'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'consumption'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'start'*** -- *required* --

The following can be defined either under 'specified_points' or 'perimeter'
objects, or directly under the parent 'active_areas' object

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'timeprofile'*** -- *required* --

FEPS uses a number of fire location fields, listed above under the
'consumption' section. All are optional, as the underlying FEPS module
has built-in defaults.

###### If running SEV model

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'area'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'localmet'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'frp'*** -- *optional* --
 - ***['fires'] > 'meta' > 'frp'*** -- *optional* -- used if frp isn't defined in activity object

##### dispersion

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > [required* --

The following can be defined either under 'specified_points' or 'perimeter'
objects, or directly under the parent 'active_areas' object

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'timeprofile'*** -- *required* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > 'utc_offset'*** -- *optional* -- hours off UTC; default: 0.0

###### if running hysplit dispersion:

- ***'met' > 'files'*** -- *required* -- array of met file objects, each containing 'first_hour', 'last_hour', and 'file' keys
  - ***['fires'] > ['activity'] > 'plumerise'*** -- *required* --
 - ***'met' > 'grid' > 'spacing'*** -- *required* if not specified in config (see below) --
 - ***'met' > 'grid' > 'boundary' > 'sw' > 'lat'*** -- *required* if not specified in config (see below) --
 - ***'met' > 'grid' > 'boundary' > 'sw' > 'lng'*** -- *required* if not specified in config (see below) --
 - ***'met' > 'grid' > 'boundary' > 'ne' > 'lat'*** -- *required* if not specified in config (see below) --
 - ***'met' > 'grid' > 'boundary' > 'ne' > 'lng'*** -- *required* if not specified in config (see below) --
 - ***'met' > 'grid' > 'domain'*** -- *optional* -- default: 'LatLng' (which means the spacing is in degrees)
 - ***'run_id'*** -- *optional* -- guid or other identifer to be used as output directory name; if not defined, generates new guid

###### if running vsmoke dispersion:

 - ***['fires'] > 'meta' > 'vsmoke' > 'ws'*** -- *required* -- wind speed
 - ***['fires'] > 'meta' > 'vsmoke' > 'wd'*** -- *required* -- wind direction
 - ***['fires'] > 'meta' > 'vsmoke' > 'stability'*** -- *optional* -- stability
 - ***['fires'] > 'meta' > 'vsmoke' > 'mixht'*** -- *optional* -- mixing height
 - ***['fires'] > 'meta' > 'vsmoke' > 'temp'*** -- *optional* -- surface temperature
 - ***['fires'] > 'meta' > 'vsmoke' > 'pressure'*** -- *optional* -- surface pressure
 - ***['fires'] > 'meta' > 'vsmoke' > 'rh'*** -- *optional* -- surface relative humidity
 - ***['fires'] > 'meta' > 'vsmoke' > 'sun'*** -- *optional* -- is fire during daylight hours or nighttime
 - ***['fires'] > 'meta' > 'vsmoke' > 'oyinta'*** -- *optional* -- initial horizontal dispersion
 - ***['fires'] > 'meta' > 'vsmoke' > 'ozinta'*** -- *optional* -- initial vertical dispersion
 - ***['fires'] > 'meta' > 'vsmoke' > 'bkgpm'*** -- *optional* -- background PM 2.5
 - ***['fires'] > 'meta' > 'vsmoke' > 'bkgco'*** -- *optional* -- background CO

##### visualization

###### if visualizing hysplit dispersion:

 - ***'dispersion' > 'model'*** -- *required* --
 - ***'dispersion' > 'output' > 'directory'*** -- *required* --
 - ***'dispersion' > 'output' > 'grid_filename'*** -- *required* --


Looking up fuelbeds requires either point data:

 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lat'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'lng'*** -- *required* (if not specifying perimeter) --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] > 'area'*** -- *required* (if not specifying perimeter) --

or perimeter data

 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'polygon'*** -- *required* (if not specifying point data) --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'perimeter' > 'area'*** -- *required* (if not specifying point data) --

other fields

 - ***['fires'] > 'id'*** -- *required* --
 - ***['fires'] > 'type'*** -- *optional* --
 - ***['fires'] > 'event_of' > 'name'*** -- *optional* --
 - ***['fires'] > 'event_of' > 'id'*** -- *optional* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > ['fuelbeds'[] > 'emissions'*** -- *optional* --
 - ***['fires'] > ['activity'] > ['active_areas'] > ['specified_points'] | 'perimeter' > ['fuelbeds'] > 'fccs_id'*** -- *optional* --
 - ***['fires'] > ['activity'] > ['active_areas'] > 'start'*** -- *required* --
 - ***'run_id'*** -- *optional* -- guid or other identifer to be used as output directory name; if not defined, generates new guid

##### export

 - ***'dispersion' > 'output'*** -- *optional* -- if 'dispersion' is in the 'extra_exports' config setting (see below), its output files will be exported along with the bsp's json output data
 - ***'visualization' > 'output'*** -- *optional* -- if 'visualization' is in the 'extra_exports' config setting (see below), its output files will be exported along with the bsp's json output data

###### if saving locally or uploading:

 - ***'run_id'*** -- *optional* -- guid or other identifer to be used as output directory name; if not defined, generates new guid

