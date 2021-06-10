# Plume Merge

Plume merge was developed to reduce HYSPLIT runtime caused by high number of emission sources.  Given a grid defined in the bluesky configuration, fire locations (i.e. `specified_points`) within each grid cell are grouped together and their plumes are merged (described below).

Example grid configuration:

            "plume_merge": {
                "grid": {
                    "spacing": 0.01,
                    "projection": "LatLon",
                    "boundary": {
                        "ne": {"lat": 36.65, "lng": -115.2},
                        "sw": {"lat": 31.95, "lng": -120.8}
                    }
                }
            },

## Merge Algorithm

After bucketing plumes by grid cell, the plumes are merged hour by hour. The hourly merge process includes determining a) height values, b) emission fractions, and c) total PM2.5.

### Height determination

Height values for the merged plume are computed by getting the min and max heights accross all plumes in the grid cell and then filling in equally spaced heights.  For example, If one plume's heights are

    "heights": [90, 250, 300, 325, 350],

and a second plume's heights are

    "heights": [100,200,300,400,500],

the merged plume would have min height 90m, max height 500m, and three heights in between spaced (500m - 90m) / 4 = 102.5m apart.

    "heights": [90.0, 192.5, 295.0, 397.5, 500.0],

### Emissions Allocation

The first step in determining emissions fractions for the merged plume is to allocate the hour's emissions, for each plume to be merged, across the plume's vertical space. Since plumerise gives us N+1 heights and N emissions fractions, the nth emission fraction is associated with the midpoint of the nth and (n+1)th heights.  For example, suppose a plume hour has 10 tons of PM25 with heights

    "heights": [100, 200, 300, 400, 500],

and fractions

    "emission_fractions": [0.4, 0.2, 0.2, 0.2],

The midpoint heights with associated emissions would be:

 - 4 tons @ 150m   <-- 10tons * 0.4 = 4 tons @ (100m + 200m) / 2 = 150m
 - 2 tons @ 250m
 - 2 tons @ 350m
 - 2 tons @ 450m

These emissions & height associations are computed for all plumes to be merged. The emissions + height pairs from all plumes are then combined and  bucketed according to the already computed merged plume heights. Finally, the pm2.5 values within each bucket are summed, and then fractions are computed.  This is all illustrated in the example below.

### Example

Fire A 12:00 plume hour

    "PM2.5": 10.0
    "emission_fractions": [0.4, 0.2, 0.2, 0.2],
    "heights": [90, 250, 300, 325, 350],

Fire B 12:00 plume hour

    "PM2.5": 2.5
    "emission_fractions": [0.1,0.3,0.4,0.2],
    "heights": [100,200,300,400,500],

Min height = 90; max height = 500; spacing = (500m - 90m) / 4 = 102.5m.
So, the heights of the merged plume are

    "heights": [90.0, 192.5, 295.0, 397.5, 500.0],


Fire A's height midpoints and allocated emissions:

    4 tons @ 170m  <-- 0.4 * 10 tons @ 250m+90m / 2
    2 tons @ 275m
    2 tons @ 312.5m
    2 tons @ 337.5m

Fire B's

    0.25 ton @ 150m  <-- 0.1 * 2.5 tons @ (100m + 200m) / 2
    0.75 ton @ 250m
    1.0 ton @ 350m
    0.5 ton @ 450m

Combined and bucketed:

 - between 90.0m and 192.5m (the 1st and 2nd heights in the merged plume)
   - 0.25 ton @ 150m
   - 4 tons @ 170m
 - between 192.5m and 295.0
   - 0.75 ton @ 250m
   - 2 tons @ 275m
 - between 295.0 and 397.5
    2 tons @ 312.5m
    2 tons @ 337.5m
    1.0 ton @ 350m
 - between 397.5m and 500.0m
    0.5 ton @ 450m

Summed:
 - between 90.0m and 192.5m -> 4.25 tons
 - between 192.5m and 295.0 -> 2.75 tons
 - between 295.0 and 397.5 -> 5 tons
 - between 397.5m and 500.0m -> 0.5 tons

Divide each by 12.5 tons total to get fractions

 - 4.25 tons / 12.5 tons = 0.34
 - 2.75 tons / 12.5 tons = 0.22
 - 5 tons / 12.5 tons = 0.4
 - 0.5 tons / 12.5 tons = 0.04

So the merged plume has the following total PM2.5, heights, and emissions fractions:


    "PM2.5": 12.5
    "emission_fractions": [0.34, 0.22, 0.4, 0.04],
    "heights": [90.0, 192.5, 295.0, 397.5, 500.0],
