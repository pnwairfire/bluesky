# Generating sql data file from shapefile

To more quickly determine if a point is within any polygons in
the ecoregions shapefile, you can load the data in the shapefile
into a postgres db and query the db.

## Install postgis

See [http://postgis.net/install/](http://postgis.net/install/)

On a Mac, you can use homebrew:

    brew install postgis

## generate sql

    cd /path/to/pnwairfire-bluesky/bluesky/ecoregion/data/
    shp2pgsql -s 4326 3ecoregions.shp > 3ecoregions.sql

## Load the data into a postgres db

....

## query the db

e.g. from stackoverflow.com/questions/7861196/check-if-a-geopoint-with-latitude-and-longitude-is-within-a-shapefile

    SELECT *
    FROM shapes
    WHERE ST_Contains(geom,ST_SetSRID(ST_MakePoint(45,-117),4326));
