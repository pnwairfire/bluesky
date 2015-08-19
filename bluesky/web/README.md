# BlueSky Web

## APIs

### POST /api/v1/run/

This API requires posted JSON with two top level keys - 'modules' and 'fires'.
The 'fires' key lists the one or more fires to process. The 'modules' key is
the order specific list of modules through which the fires should be run.

What data is needed for each fire depends on what modules are to be run.
Generally, the further you are along the pipeline of modules, the more data you
need.  (This is not entiredly true, since some data required by earlier modules
can be dropped when you pipe the fire data into later modules.)

#### Example - running ```fuelbeds```, ```consumption```, and ```emissions```:

This example requires very little data, since it's starting off with ```fuelbeds```,
one of the earlier modules in the pipeline.

    $ curl 'http://hostname/api/v1/run/' -H 'Content-Type: application/json' -d '
    {
        "modules": ["fuelbeds", "consumption", "emissions"],
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "perimeter": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [-121.4522115, 47.4316976],
                                    [-121.3990506, 47.4316976],
                                    [-121.3990506, 47.4099293],
                                    [-121.4522115, 47.4099293],
                                    [-121.4522115, 47.4316976]
                                ]
                            ]
                        ]
                    },
                    "ecoregion": "southern"
                }
            }
        ]
    }'

Another exmaple, with fire location data specified as lat + lng + size

    $ curl 'http://hostname/api/v1/run/' -H 'Content-Type: application/json' -d '
    {
        "modules": ["fuelbeds", "consumption", "emissions"],
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200
                }
            }
        ]
    }'

#### Example - running  ```timeprofile```, ```plumerise```, and ```hysplit```:

This example assumes you've already run up through emissions.  The consumption data
that would have nested along side the emissions data has been stripped out, since
it's not needed.

    $ curl 'http://hostname/api/v1/run/' -H 'Content-Type: application/json' -d '
    {
        "modules": ["timeprofile", "plumerise", "hysplit"],
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200
                },
                "fuelbeds": [
                    {
                        "fccs_id": "49",
                        "pct": 50.0,
                        "emissions": {
                            'ground fuels': {
                                'basal accumulations': {
                                    'flaming': {
                                        'PM2.5': [
                                            3.3815120047017005e-05
                                        ]
                                    },
                                    'residual': {
                                        'PM2.5': [4.621500211796271e-01]
                                    },
                                    'smoldering': {
                                        'PM2.5': [6.424985839975172e-06]
                                    }
                                }
                            }
                            /* ... (other emissions data) ... */
                        }
                    }
                ],
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150121T000000Z"
                }
            }
        ]
    }'

The nested keys in the emissions data are arbitrary.  The timeprofile
module simply expects a hierarchy of keys.  Generally speaking, the hiearchy
is of the form:

    'emissions' > 'category' > 'subcategory' > 'phase' > 'species'

The fact that the emissions data is in an array is because the consumptions
module (more specifically, the underlying 'consume' module) outputs arrays.
The length of the array equals the number of fuelbeds passed into consume.
Since consume is called on each fuelbed separately, the arrays of consumption
and emissions data are all length 1.

Other fields:

 - Met Domain

#### Example - running ```ingestion```, ```fuelbeds```, ```consumption```, ```emissions```, ```timeprofile```, ```plumerise```, and ```hysplit```:

    $ curl 'http://hostname/api/v1/run/' -H 'Content-Type: application/json' -d '
    {
        "modules": ["timeprofile", "plumerise", "hysplit"],
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200
                }
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150121T000000Z"
                }
            }
        ]
    }
