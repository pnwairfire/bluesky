## Examples

The examples listed here are based on **proposed** changes to the code base.  They
do not represent the current behavior.

### Through Emissions

Assume you have the following input data:

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "activity": [
                    {
                        "collection_name": "First day",
                        "active_areas": [
                            {
                                "start": "2015-01-20T17:00:00",
                                "end": "2015-01-21T17:00:00",
                                "ecoregion": "southern",
                                "utc_offset": "-09:00"
                                "specified_points": [
                                    {
                                        "name": "HMW-32434",
                                        "lat": 47.41,
                                        "lng": -121.41,
                                        "area": "120"
                                    },
                                    {
                                        "lat": 47.42,
                                        "lng": -121.43,
                                        "area": "103"
                                    }
                                ],
                                "perimeter_polygon": [
                                    [-121.45, 47.43],
                                    [-121.39, 47.43],
                                    [-121.39, 47.40],
                                    [-121.45, 47.40],
                                    [-121.45, 47.43]
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

Lets say that's in a file called locations.json. piping that into bsp
and running it through ingestion

    cat ./tmp/locations.json | bsp ingestion

would give you:


    # TODO: fill in output


Piping that through fuelbeds

    cat ./tmp/locations.json | bsp ingestion fuelbeds
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds

would give you:

    # TODO: fill in output

Piping that through consumption

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption

would give you:

    # TODO: fill in output


Finally, piping that through emissions

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption emissions
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption | bsp emissions

would give you:

    # TODO: fill in output
