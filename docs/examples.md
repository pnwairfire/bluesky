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
                        "name": "First day",
                        "active_areas": [
                            {
                                "start": "2015-08-04T17:00:00",
                                "end": "2015-08-05T17:00:00",
                                "utc_offset": "-09:00",
                                "country": "USA",
                                "state": "WA",
                                "ecoregion": "western",
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
                                        "area": "103",
                                        /* ecoregion and other input fields can
                                           be defined either per location or
                                           in the parent active area object */
                                        "ecoregion": "western"
                                    }
                                ],
                                "perimeter": {
                                    "polygon": [
                                        [-121.45, 47.43],
                                        [-121.39, 47.43],
                                        [-121.39, 47.40],
                                        [-121.45, 47.40],
                                        [-121.45, 47.43]
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

Lets say that's in a file called fires.json. piping that into bsp
and running it through fuelbeds

    cat ./tmp/fires.json | bsp fuelbeds

would give you:

    # TODO: fill in output

Piping that through consumption

    cat ./tmp/fires.json | bsp fuelbeds consumption
    # or
    cat ./tmp/fires.json | bsp fuelbeds |bsp consumption

would give you:

    # TODO: fill in output

Finally, piping that through emissions

    cat ./tmp/fires.json fuelbeds consumption emissions
    # or
    cat ./tmp/fires.json | bsp fuelbeds |bsp consumption | bsp emissions

would give you:

    # TODO: fill in output
